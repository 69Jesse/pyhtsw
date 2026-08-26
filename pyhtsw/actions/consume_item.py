from typing import final

from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

from ..expression.expression import Expression

__all__ = (
    'ConsumeItemExpression',
    'consume_item',
)


@final
class ConsumeItemExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='USE_HELD_ITEM',
        limit=1,
        effects=Effects.of(reads=(Resource.INVENTORY,), writes=(Resource.INVENTORY,)),
        display_name='Use/Remove Held Item',
        item_only=True,
    )

    def into_htsl(self) -> str:
        return 'consumeItem'


def consume_item() -> None:
    ConsumeItemExpression().write()
