from collections.abc import Generator
from typing import TYPE_CHECKING, NamedTuple

from pyhtsw.compiler.module_export import importable_blocks, walk_expressions
from pyhtsw.expression.condition.conditional_expression import ConditionalExpression

if TYPE_CHECKING:
    from pyhtsw.compiler.importable import Importable
    from pyhtsw.expression.expression import Expression

__all__ = (
    'UndeclaredReferenceError',
    'check_declared_references',
)


class UndeclaredReferenceError(RuntimeError):
    """An exclusive project names a function, menu, region, team or group it
    does not declare, so htsw's prune would delete the target."""


class UndeclaredReference(NamedTuple):
    block: str
    kind: str
    name: str
    rendered: str


DECLARE_WITH: dict[str, str] = {
    'functions': '@function',
    'menus': 'Menu',
    'regions': 'Region',
    'teams': 'Team',
    'groups': 'Group',
}
BUILT_IN_NAMES: dict[str, frozenset[str]] = {'teams': frozenset(('none',))}


def _normalize(name: str) -> str:
    return name.strip().lower()


def find_undeclared_references(
    importables: list['Importable'],
) -> list[UndeclaredReference]:
    declared: dict[str, set[str]] = {kind: set() for kind in DECLARE_WITH}
    for importable in importables:
        if importable.kind in declared:
            declared[importable.kind].add(_normalize(importable.identifier()))

    found: list[UndeclaredReference] = []
    seen: set[tuple[str, str, str]] = set()
    for importable in importables:
        for block in importable_blocks(importable):
            for expression in walk_expressions(block.expressions):
                for kind, name, rendered in _references(expression):
                    if kind not in declared or not name.strip():
                        continue
                    normalized = _normalize(name)
                    if normalized in BUILT_IN_NAMES.get(kind, ()):
                        continue
                    if normalized in declared[kind]:
                        continue
                    key = (block.get_name(), kind, name)
                    if key in seen:
                        continue
                    seen.add(key)
                    found.append(
                        UndeclaredReference(block.get_name(), kind, name, rendered),
                    )
    return found


def _references(expression: 'Expression') -> Generator[tuple[str, str, str]]:
    if isinstance(expression, ConditionalExpression):
        for condition in expression.conditions:
            for kind, name in condition.referenced_importables():
                yield kind, name, condition.into_htsl()
        return
    for kind, name in expression.referenced_importables():
        yield kind, name, expression.into_htsl()


def check_declared_references(importables: list['Importable']) -> None:
    found = find_undeclared_references(importables)
    if not found:
        return
    lines = [
        f'  {ref.block}: {ref.kind[:-1]} "{ref.name}" ({ref.rendered})' for ref in found
    ]
    kinds = sorted({ref.kind for ref in found}, key=list(DECLARE_WITH).index)
    hint = ', '.join(f'{DECLARE_WITH[kind]}(...)' for kind in kinds)
    raise UndeclaredReferenceError(
        'exclusive_house is set, so htsw would delete everything the project '
        'does not declare, and these references would then point at nothing:\n'
        + '\n'.join(lines)
        + f'\nDeclare them ({hint}) instead of referencing them by name, or '
        'drop exclusive_house.',
    )
