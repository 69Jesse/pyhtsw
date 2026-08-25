from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with

from ..expression.expression import Expression
from .item import Item, item_action_reference, item_referenced_importables

__all__ = (
    'RemoveItemExpression',
    'remove_item',
)


@final
class RemoveItemExpression(Expression):
    item: Item | type[Item]

    def __init__(self, item: Item | type[Item]) -> None:
        self.item = item

    def into_htsl(self) -> str:
        name = item_action_reference(self.item)
        return f'removeItem {self.inline_quoted(name)}'

    def referenced_importables(self) -> list[tuple[str, str]]:
        return item_referenced_importables(self.item)

    def cloned(
        self,
        *,
        item: Item | type[Item] | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'item': item,
            },
        )

    def equals(self, other: object) -> bool:
        if not isinstance(other, RemoveItemExpression):
            return False
        return self.item == other.item

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.item}>'


def remove_item(item: Item | type[Item]) -> None:
    RemoveItemExpression(item=item).write()
