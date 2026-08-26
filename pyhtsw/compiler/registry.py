from collections.abc import Generator
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pyhtsw.compiler.schedule import Effects, ResourceKey

if TYPE_CHECKING:
    from pyhtsw.expression.condition.condition import Condition
    from pyhtsw.expression.expression import Expression
    from pyhtsw.placeholders.base import PlaceholderCheckable

__all__ = (
    'ActionMeta',
    'ConditionMeta',
    'iter_action_types',
    'iter_condition_types',
    'iter_placeholder_types',
)


@dataclass(frozen=True, slots=True)
class ActionMeta:
    """What the compiler knows about one action or placeholder type, declared on
    the class itself. The default answers are the safe ones: no htsw identity,
    no limit, unknown effects (a full reorder barrier)."""

    htsw_name: str | None = None
    limit: int | None = None
    effects: Effects | None = None
    control: bool = False
    display_name: str | None = None
    item_only: bool = False
    menu_only: bool = False
    forbidden_in_events: bool = False
    forbidden_events: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ConditionMeta:
    htsw_name: str | None = None
    limit: int | None = None
    reads: frozenset[ResourceKey] | None = None
    display_name: str | None = None
    scoped_events: tuple[str, ...] = ()


def _walk[T](cls: type[T]) -> Generator[type[T]]:
    yield cls
    for sub in cls.__subclasses__():
        yield from _walk(sub)


def iter_action_types() -> Generator[type['Expression']]:
    from pyhtsw.expression.expression import Expression

    yield from _walk(Expression)


def iter_condition_types() -> Generator[type['Condition']]:
    from pyhtsw.expression.condition.condition import Condition

    yield from _walk(Condition)


def iter_placeholder_types() -> Generator[type['PlaceholderCheckable']]:
    from pyhtsw.placeholders.base import PlaceholderCheckable

    yield from _walk(PlaceholderCheckable)
