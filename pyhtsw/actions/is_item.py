from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.registry import ConditionMeta
from pyhtsw.schedule import Resource

from ..expression.condition.condition import Condition
from ..types import ITEM_CHECK_WHAT, ITEM_CHECK_WHERE, ITEM_REQUIRED_AMOUNT
from .item import Item, item_action_reference, item_referenced_importables

__all__ = ('IsItem',)


@final
class IsItem(Condition):
    htsw_meta = ConditionMeta(
        htsw_name='IS_ITEM',
        limit=20,
        reads=frozenset((Resource.INVENTORY,)),
        display_name='Is Item',
        scoped_events=(
            'Player Drop Item',
            'Player Pick Up Item',
            'Player Change Held Item',
        ),
    )

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
        return (
            f'isItem {self.inline_quoted(name)} '
            f'{self.inline(self.what_to_check)} '
            f'{self.inline(self.where_to_check)} '
            f'{self.inline(self.required_amount)}'
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
