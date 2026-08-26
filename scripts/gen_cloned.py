import argparse
import ast
import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pyhtsw  # noqa: E402, F401
from pyhtsw.base_object import BaseObject  # noqa: E402

# Clones that are deliberately hand-written.
HAND_WRITTEN = {
    ('pyhtsw.declarations.item', 'Item'),
    ('pyhtsw.actions.flow', 'IfContextManager'),
}
ANCHORS = ('equals', 'equals_raw', '__repr__')
SHARED = ('Missing', 'MISSING', 'clone_with')


def walk(cls):
    yield cls
    for sub in cls.__subclasses__():
        yield from walk(sub)


def targets():
    seen = {}
    for cls in walk(BaseObject):
        if inspect.isabstract(cls) or not cls.__clone_fields__:
            continue
        if (cls.__module__, cls.__name__) in HAND_WRITTEN:
            continue
        seen[(cls.__module__, cls.__name__)] = cls
    return sorted(seen.values(), key=lambda c: (c.__module__, c.__name__))


def class_node(tree, name):
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    return None


def init_owner(cls):
    for klass in cls.__mro__:
        init = klass.__dict__.get('__init__')
        if init is not None and hasattr(init, '__code__'):
            return klass
    return None


def annotations_of(cls):
    owner = init_owner(cls)
    if owner is None:
        return {}
    owner_path = inspect.getsourcefile(owner)
    if owner_path is None:
        return {}
    src = Path(owner_path).read_text(encoding='utf-8')
    node = class_node(ast.parse(src), owner.__name__)
    if node is None:
        return {}
    for fn in node.body:
        if isinstance(fn, ast.FunctionDef) and fn.name == '__init__':
            args = fn.args
            out = {}
            for arg in [*args.posonlyargs, *args.args, *args.kwonlyargs]:
                if arg.annotation is not None:
                    out[arg.arg] = ast.get_source_segment(src, arg.annotation)
            return out
    return {}


def carry_annotations(cls):
    out = {}
    for name in cls.__clone_carry__:
        if name.startswith('_'):
            continue
        for klass in cls.__mro__:
            path = inspect.getsourcefile(klass)
            if path is None:
                continue
            src = Path(path).read_text(encoding='utf-8')
            node = class_node(ast.parse(src), klass.__name__)
            if node is None:
                continue
            for stmt in node.body:
                if (
                    isinstance(stmt, ast.AnnAssign)
                    and isinstance(stmt.target, ast.Name)
                    and stmt.target.id == name
                ):
                    out[name] = ast.get_source_segment(src, stmt.annotation)
                    break
            if name in out:
                break
    return out


def union_with_missing(ann):
    """`str | None` -> `str | None | Missing`, preserving quoted forward refs."""
    ann = ann.strip()
    if len(ann) > 1 and ann[0] in ('"', "'") and ann[-1] == ann[0]:
        return "'" + ann[1:-1] + " | Missing'"
    return ann + ' | Missing'


def names_in(ann):
    try:
        tree = ast.parse(ann.strip('"\''), mode='eval')
    except SyntaxError:
        return set()
    return {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}


def render(cls):
    fields = list(cls.__clone_fields__)
    carry = [c for c in cls.__clone_carry__ if not c.startswith('_')]
    anns = annotations_of(cls)
    anns.update(carry_annotations(cls))
    used = set()
    lines = ['    def cloned(', '        self,', '        *,']
    for name in fields + carry:
        ann = anns.get(name)
        if ann is None:
            lines.append('        ' + name + ': Any | Missing = MISSING,')
            used.add('Any')
        else:
            lines.append(
                '        ' + name + ': ' + union_with_missing(ann) + ' = MISSING,',
            )
            used |= names_in(ann)
    lines += [
        '    ) -> Self:',
        '        return clone_with(',
        '            self,',
        '            {',
    ]
    for name in fields + carry:
        lines.append("                '" + name + "': " + name + ',')
    lines += ['            },', '        )']
    return '\n'.join(lines) + '\n', used


def insertion_line(node):
    """Line to insert at, and whether an anchor method follows it. Without an
    anchor the method lands at the end of the class body, which needs its own
    leading blank line or `ruff format` adds one and the next run diverges."""
    for stmt in node.body:
        if isinstance(stmt, ast.FunctionDef) and stmt.name in ANCHORS:
            return min([d.lineno for d in stmt.decorator_list] + [stmt.lineno]), True
    last = node.body[-1]
    return (last.end_lineno or last.lineno) + 1, False


def bound_names(tree):
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            out |= {a.asname or a.name for a in node.names}
        elif isinstance(node, ast.Import):
            out |= {(a.asname or a.name).split('.')[0] for a in node.names}
        elif isinstance(node, ast.ClassDef | ast.FunctionDef):
            out.add(node.name)
    return out


_INDEX = None


def source_index():
    """name -> defining pyhtsw module, for aliases that carry no __module__."""
    global _INDEX
    if _INDEX is not None:
        return _INDEX
    _INDEX = {}
    for path in sorted((ROOT / 'pyhtsw').rglob('*.py')):
        dotted = '.'.join(path.relative_to(ROOT).with_suffix('').parts)
        try:
            tree = ast.parse(path.read_text(encoding='utf-8'))
        except SyntaxError:
            continue
        exported = set()
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == '__all__' for t in node.targets
            ):
                exported = {
                    e.value
                    for e in getattr(node.value, 'elts', [])
                    if isinstance(e, ast.Constant) and isinstance(e.value, str)
                }
        for node in tree.body:
            bound = []
            if isinstance(node, ast.ClassDef | ast.FunctionDef):
                bound = [node.name]
            elif isinstance(node, ast.Assign):
                bound = [t.id for t in node.targets if isinstance(t, ast.Name)]
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                bound = [node.target.id]
            for name in bound:
                if name.startswith('_'):
                    continue
                if name not in _INDEX or name in exported:
                    _INDEX[name] = dotted
    return _INDEX


def module_of(name):
    for mod in list(sys.modules.values()):
        mod_name = getattr(mod, '__name__', '')
        if not mod_name.startswith('pyhtsw'):
            continue
        obj = getattr(mod, name, None)
        if obj is None:
            continue
        owner = getattr(obj, '__module__', None)
        if owner and owner.startswith('pyhtsw'):
            return owner
    return source_index().get(name)


def strip_existing(src, classes):
    tree = ast.parse(src)
    lines = src.splitlines(keepends=True)
    cuts = []
    for cls in classes:
        node = class_node(tree, cls.__name__)
        if node is None:
            continue
        for fn in node.body:
            if isinstance(fn, ast.FunctionDef) and fn.name == 'cloned':
                start = min([d.lineno for d in fn.decorator_list] + [fn.lineno])
                end = fn.end_lineno or start
                while end < len(lines) and lines[end].strip() == '':
                    end += 1
                begin = start - 1
                while begin > 0 and lines[begin - 1].strip() == '':
                    begin -= 1
                cuts.append((begin, end))
    if not cuts:
        return src
    keep = [True] * len(lines)
    for a, b in cuts:
        for i in range(a, b):
            keep[i] = False
    return ''.join(line for line, k in zip(lines, keep, strict=True) if k)


def rendered_file(path, classes):
    dotted = '.'.join(path.relative_to(ROOT).with_suffix('').parts)
    original = path.read_text(encoding='utf-8')
    src = strip_existing(original, classes)
    needed = {'Self', *SHARED}
    edits = []
    tree = ast.parse(src)
    for cls in classes:
        node = class_node(tree, cls.__name__)
        if node is None:
            continue
        body, used = render(cls)
        line, anchored = insertion_line(node)
        edits.append((line, body + '\n' if anchored else '\n' + body))
        needed |= used

    lines = src.splitlines(keepends=True)
    for line, body in sorted(edits, reverse=True):
        lines.insert(line - 1, body)
    out = ''.join(lines)

    have = bound_names(ast.parse(out))
    imports = []
    typing_add = [n for n in ('Any', 'Self') if n in needed and n not in have]
    if typing_add:
        imports.append('from typing import ' + ', '.join(typing_add))
    clone_add = [n for n in SHARED if n not in have]
    if clone_add:
        imports.append('from pyhtsw.clone import ' + ', '.join(sorted(clone_add)))
    for name in sorted(needed - have - {'Any', 'Self'} - set(SHARED)):
        mod = module_of(name)
        if mod and mod != dotted:
            imports.append('from ' + mod + ' import ' + name)
    if imports:
        insert_at = 0
        for node in ast.parse(out).body:
            if isinstance(node, ast.Import | ast.ImportFrom):
                insert_at = node.end_lineno or insert_at
        out_lines = out.splitlines(keepends=True)
        out_lines.insert(insert_at, ''.join(i + '\n' for i in imports))
        out = ''.join(out_lines)
    return original, out


def ruff_pipeline(source, path):
    """The same `ruff check --fix` + `ruff format` the write path applies, so
    --check compares like for like instead of reporting formatting as drift."""
    for cmd in (
        ['ruff', 'check', '--fix', '-q', '--stdin-filename', str(path), '-'],
        ['ruff', 'format', '-q', '--stdin-filename', str(path), '-'],
    ):
        result = subprocess.run(
            cmd,
            cwd=ROOT,
            input=source,
            capture_output=True,
            text=True,
            encoding='utf-8',
            check=False,
        )
        if result.returncode == 2:
            raise RuntimeError(' '.join(cmd) + ': ' + result.stderr.strip())
        if result.stdout:
            source = result.stdout
    return source


def generate(write):
    by_file = {}
    for cls in targets():
        path = inspect.getsourcefile(cls)
        if path is None:
            continue
        by_file.setdefault(Path(path), []).append(cls)

    stale = []
    written = []
    count = 0
    for path, classes in sorted(by_file.items()):
        src, out = rendered_file(path, classes)
        count += len(classes)
        if not write:
            out = ruff_pipeline(out, path)
        if out == src:
            continue
        if write:
            path.write_text(out, encoding='utf-8')
            written.append(str(path))
        else:
            stale.append(str(path.relative_to(ROOT)))
    return count, stale, written


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    count, stale, written = generate(write=not args.check)
    if args.check:
        if stale:
            print('stale generated cloned() signatures in:')
            for path in stale:
                print('  ' + path)
            print('\nrun: python scripts/gen_cloned.py')
            return 1
        print(str(count) + ' generated cloned() signatures are up to date')
        return 0
    print('generated ' + str(count) + ' cloned() signatures')
    if written:
        # Only the files actually rewritten, so an unrelated unformatted file
        # elsewhere in the package is not dragged into the diff.
        subprocess.run(
            ['ruff', 'check', '--fix', '-q', *written],
            cwd=ROOT,
            check=False,
        )
        subprocess.run(['ruff', 'format', '-q', *written], cwd=ROOT, check=False)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
