from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from pyhtsw.expression.expression import Expression


__all__ = (
    'StrictOrder',
    'strict_order',
    'strict_order_region_of',
    'tag_strict_order_region',
)


# Set on an expression written inside a `strict_order()` block. The scheduler
# treats a tagged expression as an ordering barrier, so the region keeps its
# order internally and nothing from outside moves through it. Wrapping it in a
# conditional or carving it into an overflow function is still allowed - neither
# changes behaviour, and forbidding them would let the escape hatch reintroduce
# the limit errors it is meant to work around.
STRICT_ORDER_ATTRIBUTE = '_strict_order_region'


class StrictOrder:
    _stack: ClassVar[list[int]] = []
    _counter: ClassVar[int] = 0

    def __enter__(self) -> None:
        StrictOrder._counter += 1
        StrictOrder._stack.append(StrictOrder._counter)

    def __exit__(self, *args: object) -> None:
        StrictOrder._stack.pop()


def strict_order() -> StrictOrder:
    return StrictOrder()


def current_strict_order_region() -> int | None:
    return StrictOrder._stack[-1] if StrictOrder._stack else None


def tag_strict_order_region(expression: 'Expression', region: int | None) -> None:
    if region is not None:
        setattr(expression, STRICT_ORDER_ATTRIBUTE, region)


def strict_order_region_of(expression: 'Expression') -> int | None:
    return getattr(expression, STRICT_ORDER_ATTRIBUTE, None)
