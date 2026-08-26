from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from .block import Block
    from .expression.expression import Expression
    from .importable import Importable
    from .limits import ImportableKind
    from .registry import ActionMeta

__all__ = (
    'ScopeError',
    'ScopeViolation',
    'check_scopes',
)


class ScopeError(RuntimeError):
    """An action was written into a container that cannot hold it."""


class ScopeViolation(NamedTuple):
    where: str
    message: str


CANCELLABLE_EVENTS: frozenset[str] = frozenset(
    {
        'Player Death',
        'Fish Caught',
        'Player Damage',
        'Player Drop Item',
        'Player Pick Up Item',
        'Player Change Held Item',
        'Player Toggle Sneak',
        'Player Toggle Flight',
    },
)

_STRUCTURAL: 'tuple[frozenset[type], type, type] | None' = None


def _structural() -> 'tuple[frozenset[type], type, type]':
    global _STRUCTURAL
    if _STRUCTURAL is not None:
        return _STRUCTURAL

    from .actions.cancel_event import CancelEventExpression
    from .actions.exit_function import ExitFunctionExpression
    from .actions.random import RandomExpression
    from .expression.condition.conditional_expression import ConditionalExpression

    _STRUCTURAL = (
        frozenset({ConditionalExpression, RandomExpression}),
        CancelEventExpression,
        ExitFunctionExpression,
    )
    return _STRUCTURAL


def _meta(cls: object) -> 'ActionMeta':
    from .registry import ActionMeta

    meta = getattr(cls, 'htsw_meta', None)
    if not isinstance(meta, ActionMeta):
        return ActionMeta()
    return meta


def _name(cls: object) -> str:
    return _meta(cls).display_name or getattr(cls, '__name__', str(cls))


def _check_conditions(
    expression: 'Expression',
    *,
    event: str | None,
    report: 'list[str]',
) -> None:
    from .expression.condition.conditional_expression import ConditionalExpression

    if not isinstance(expression, ConditionalExpression):
        return

    for condition in expression.conditions:
        meta = type(condition).htsw_meta
        allowed = meta.scoped_events
        if not allowed or (event is not None and event in allowed):
            continue
        name = meta.display_name or type(condition).__name__
        context = f'{event} event' if event else 'this context'
        report.append(
            f'{name} condition can only be used inside: '
            f'{", ".join(allowed)}. It cannot be used in {context}.',
        )


def _check_action(
    cls: object,
    *,
    kind: 'ImportableKind',
    event: str | None,
    nested: bool,
    report: 'list[str]',
) -> None:
    nestable, cancel_event, exit_cls = _structural()
    meta = _meta(cls)

    if kind == 'items' and cls in nestable:
        report.append(f'{_name(cls)} action cannot be used inside items')

    if cls is cancel_event:
        if kind != 'events':
            report.append(f'Cancel Event action cannot be used inside {kind}')
        elif event is not None and event not in CANCELLABLE_EVENTS:
            report.append(f'{event} event cannot be cancelled.')

    if meta.item_only and kind != 'items':
        report.append(
            f'{_name(cls)} action can only be used inside items, not {kind}',
        )

    if meta.menu_only and kind != 'menus':
        report.append(
            f'{_name(cls)} action can only be used inside menus, not {kind}',
        )

    if cls is exit_cls and not nested:
        report.append(
            'Exit action can only be used inside conditional or random actions',
        )

    if kind == 'events':
        if meta.forbidden_in_events:
            report.append(f'{_name(cls)} action cannot be used inside events')
        if event is not None and event in meta.forbidden_events:
            report.append(
                f'{_name(cls)} action cannot be used inside {event} events',
            )


def _walk(
    expressions: 'list[Expression]',
    *,
    kind: 'ImportableKind',
    event: str | None,
    nested: bool,
    report: 'list[str]',
) -> None:
    from .limits import Counter, nesting_of

    counter = Counter(importable=kind)
    for expression in expressions:
        for cls in counter.action_counts(expression):
            _check_action(
                cls,
                kind=kind,
                event=event,
                nested=nested,
                report=report,
            )
        _check_conditions(expression, event=event, report=report)
        inner_nested = nested or nesting_of(expression) is not None
        for inner in expression.nested_expressions_refs():
            _walk(
                inner,
                kind=kind,
                event=event,
                nested=inner_nested,
                report=report,
            )


def check_scopes(
    blocks: 'list[Block]',
    importables: 'list[Importable]',
) -> list[ScopeViolation]:
    from .importable import EventImportable

    events_by_block: dict[int, str] = {
        id(importable.block): importable.event
        for importable in importables
        if isinstance(importable, EventImportable)
    }

    violations: list[ScopeViolation] = []
    for block in blocks:
        report: list[str] = []
        _walk(
            block.expressions,
            kind=block.importable_kind,
            event=events_by_block.get(id(block)),
            nested=False,
            report=report,
        )
        if not report:
            continue
        where = f'{block.importable_kind[:-1]} "{block.get_name()}"'
        for message in dict.fromkeys(report):
            violations.append(ScopeViolation(where, message))
    return violations


def raise_scope_violations(violations: list[ScopeViolation]) -> None:
    if not violations:
        return
    lines = [f'  - {violation.where}: {violation.message}' for violation in violations]
    raise ScopeError(
        'These actions are not allowed in the container they were written into:\n'
        + '\n'.join(lines),
    )
