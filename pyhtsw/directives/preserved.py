from typing import TYPE_CHECKING

from pyhtsw.directives.base import Directive

if TYPE_CHECKING:
    from pyhtsw.expression.expression import Expression


__all__ = (
    'Preserved',
    'is_preserved',
    'tag_preserved',
)


# Set on an expression written inside a `Preserved()` block: the optimizer must
# emit it exactly as written. The peephole passes and the temp-stat merge skip
# tagged expressions entirely - they may be read through runtime-composed names
# no static analysis can see, so "provably dead" or "provably equivalent" is
# never provable for them. Ordering is a separate concern: a region whose
# hidden readers also care about position wants `StrictOrder()` alongside.
PRESERVED_ATTRIBUTE = '_preserved'


class Preserved(Directive):
    pass


def currently_preserved() -> bool:
    return Preserved.active()


def tag_preserved(expression: 'Expression', active: bool) -> None:
    if active:
        setattr(expression, PRESERVED_ATTRIBUTE, True)


def is_preserved(expression: 'Expression') -> bool:
    return getattr(expression, PRESERVED_ATTRIBUTE, False)
