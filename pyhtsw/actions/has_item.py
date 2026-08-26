from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with

from ..expression.condition.condition import Condition
from ..types import ITEM_CHECK_WHAT, ITEM_CHECK_WHERE, ITEM_REQUIRED_AMOUNT
from .item import Item, item_action_reference, item_referenced_importables

__all__ = ('HasItem',)


@final
class HasItem(Condition):
    item: Item
    what_to_check: ITEM_CHECK_WHAT
    where_to_check: ITEM_CHECK_WHERE
    required_amount: ITEM_REQUIRED_AMOUNT

    def __init__(
        self,
        item: Item,
        what_to_check: ITEM_CHECK_WHAT = 'metadata',
        where_to_check: ITEM_CHECK_WHERE = 'anywhere',
        required_amount: ITEM_REQUIRED_AMOUNT = 'any_amount',
    ) -> None:
        self.item = item
        self.what_to_check = what_to_check
        self.where_to_check = where_to_check
        self.required_amount = required_amount

    def into_htsl_raw(self) -> str:
        name = item_action_reference(self.item)

        required_amount = {
            'any_amount': 'Any Amount',
            'equal_or_greater_amount': 'Equal or Greater Amount',
        }[self.required_amount]
        return (
            f'hasItem {self.inline_quoted(name)} '
            f'{self.inline(self.what_to_check)} '
            f'{self.inline(self.where_to_check)} '
            f'{self.inline_quoted(required_amount)}'
        )

    def referenced_importables(self) -> list[tuple[str, str]]:
        return item_referenced_importables(self.item)

    def cloned(
        self,
        *,
        item: Item | Missing = MISSING,
        what_to_check: ITEM_CHECK_WHAT | Missing = MISSING,
        where_to_check: ITEM_CHECK_WHERE | Missing = MISSING,
        required_amount: ITEM_REQUIRED_AMOUNT | Missing = MISSING,
        inverted: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'item': item,
                'what_to_check': what_to_check,
                'where_to_check': where_to_check,
                'required_amount': required_amount,
                'inverted': inverted,
            },
        )

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, HasItem):
            return False
        return (
            self.equals_or_eq(self.item, other.item)
            and self.what_to_check == other.what_to_check
            and self.where_to_check == other.where_to_check
            and self.required_amount == other.required_amount
        )

    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}<item={self.item!r} '
            f'what_to_check={self.what_to_check} '
            f'where_to_check={self.where_to_check} '
            f'required_amount={self.required_amount} '
            f'inverted={self.inverted}>'
        )
