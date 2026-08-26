from itertools import count
from typing import TYPE_CHECKING, ClassVar

from pyhtsw.directives.base import Directive

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pyhtsw.expression.expression import Expression


__all__ = (
    'StrictOrder',
    'strict_order_region_of',
    'tag_strict_order_region',
)


# Set on an expression written inside a `StrictOrder()` block. The scheduler
# treats a tagged expression as an ordering barrier, so the region keeps its
# order internally and nothing from outside moves through it. Wrapping it in a
# conditional or carving it into an overflow function is still allowed - neither
# changes behaviour, and forbidding them would let the escape hatch reintroduce
# the limit errors it is meant to work around.
STRICT_ORDER_ATTRIBUTE = '_strict_order_region'


class StrictOrder(Directive):
    _regions: 'ClassVar[Iterator[int]]' = count(1)

    region: int

    def __init__(self) -> None:
        self.region = next(StrictOrder._regions)


def current_strict_order_region() -> int | None:
    stack = StrictOrder._stack
    return stack[-1].region if stack else None


def tag_strict_order_region(expression: 'Expression', region: int | None) -> None:
    if region is not None:
        setattr(expression, STRICT_ORDER_ATTRIBUTE, region)


def strict_order_region_of(expression: 'Expression') -> int | None:
    return getattr(expression, STRICT_ORDER_ATTRIBUTE, None)
