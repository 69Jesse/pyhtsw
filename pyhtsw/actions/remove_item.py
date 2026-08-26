from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

from ..expression.expression import Expression
from .item import Item, item_action_reference, item_referenced_importables

__all__ = (
    'RemoveItemExpression',
    'remove_item',
)


@final
class RemoveItemExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='REMOVE_ITEM',
        limit=40,
        effects=Effects.of(reads=(Resource.INVENTORY,), writes=(Resource.INVENTORY,)),
        display_name='Remove Item',
        forbidden_events=('Player Quit',),
    )

    item: Item

    def __init__(self, item: Item) -> None:
        self.item = item

    def into_htsl(self) -> str:
        name = item_action_reference(self.item)
        return f'removeItem {self.inline_quoted(name)}'

    def referenced_importables(self) -> list[tuple[str, str]]:
        return item_referenced_importables(self.item)

    def cloned(
        self,
        *,
        item: Item | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'item': item,
            },
        )


def remove_item(item: Item) -> None:
    RemoveItemExpression(item=item).write()
