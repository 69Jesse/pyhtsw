import ast
import inspect
import shutil
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))

import pyhtsw  # noqa: E402, F401
from pyhtsw.base_object import BaseObject  # noqa: E402


def _subclasses(cls: type):
    yield cls
    for sub in cls.__subclasses__():
        yield from _subclasses(sub)


ALL = sorted(
    {(c.__module__, c.__name__): c for c in _subclasses(BaseObject)}.values(),
    key=lambda c: (c.__module__, c.__name__),
)


# Every constructor field must be readable off an instance, or clone_with raises
# AttributeError the first time anything clones that class.
def _assigned_in_init(cls: type) -> set[str]:
    names: set[str] = set()
    for klass in cls.__mro__:
        init = klass.__dict__.get('__init__')
        if init is None or not hasattr(init, '__code__'):
            continue
        try:
            tree = ast.parse(textwrap.dedent(inspect.getsource(init)))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == 'self'
                and isinstance(node.ctx, ast.Store)
            ):
                names.add(node.attr)
    return names


unreachable: list[str] = []
for cls in ALL:
    if inspect.isabstract(cls) or not cls.__clone_fields__:
        continue
    reachable = _assigned_in_init(cls) | {n for n in dir(cls) if not n.startswith('__')}
    for field in cls.__clone_fields__:
        if cls.__clone_map__.get(field, field) not in reachable:
            unreachable.append(f'{cls.__module__}.{cls.__name__}.{field}')
assert not unreachable, (
    'clone fields with no matching attribute (add a __clone_map__ entry):\n  '
    + '\n  '.join(unreachable)
)


# A carried attribute is set after construction, so it must exist too.
missing_carry: list[str] = []
for cls in ALL:
    if inspect.isabstract(cls):
        continue
    reachable = _assigned_in_init(cls) | set(dir(cls))
    for name in cls.__clone_carry__:
        if name not in reachable:
            missing_carry.append(f'{cls.__module__}.{cls.__name__}.{name}')
assert not missing_carry, 'carried attributes that no instance has:\n  ' + '\n  '.join(
    missing_carry,
)


# The generated signatures must still match what __init__ declares.
if shutil.which('ruff') is None:
    print('  (ruff not on PATH, skipping the generated-signature drift check)')
else:
    import gen_cloned  # type: ignore[import-not-found]

    count, stale, _ = gen_cloned.generate(write=False)
    assert not stale, (
        'stale generated cloned() signatures in:\n  '
        + '\n  '.join(stale)
        + '\n\nrun: python scripts/gen_cloned.py'
    )
    assert count > 0, 'the generator found no classes to generate for'
