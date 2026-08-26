from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from pyhtsw.expression.expression import Expression


__all__ = (
    'Preserved',
    'is_preserved',
    'preserved',
    'tag_preserved',
)


# Set on an expression written inside a `preserved()` block: the optimizer must
# emit it exactly as written. The peephole passes and the temp-stat merge skip
# tagged expressions entirely - they may be read through runtime-composed names
# no static analysis can see, so "provably dead" or "provably equivalent" is
# never provable for them. Ordering is a separate concern: a region whose
# hidden readers also care about position wants `strict_order()` alongside.
PRESERVED_ATTRIBUTE = '_preserved'


class Preserved:
    _depth: ClassVar[int] = 0

    def __enter__(self) -> None:
        Preserved._depth += 1

    def __exit__(self, *args: object) -> None:
        Preserved._depth -= 1


def preserved() -> Preserved:
    return Preserved()


def currently_preserved() -> bool:
    return Preserved._depth > 0


def tag_preserved(expression: 'Expression', active: bool) -> None:
    if active:
        setattr(expression, PRESERVED_ATTRIBUTE, True)


def is_preserved(expression: 'Expression') -> bool:
    return getattr(expression, PRESERVED_ATTRIBUTE, False)
