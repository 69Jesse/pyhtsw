from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.compiler.registry import ConditionMeta
from pyhtsw.compiler.schedule import Resource
from pyhtsw.declarations.item import (
    Item,
    item_action_reference,
    item_referenced_importables,
)
from pyhtsw.expression.condition.condition import Condition
from pyhtsw.generated.enums import ItemAmount, ItemLocation, ItemProperty

__all__ = (
    'HasItem',
    'IsItem',
)


@final
class HasItem(Condition):
    htsw_meta = ConditionMeta(
        htsw_name='REQUIRE_ITEM',
        limit=20,
        reads=frozenset((Resource.INVENTORY,)),
    )

    item: Item
    what_to_check: ItemProperty
    where_to_check: ItemLocation
    required_amount: ItemAmount

    def __init__(
        self,
        item: Item,
        what_to_check: ItemProperty = 'metadata',
        where_to_check: ItemLocation = 'anywhere',
        required_amount: ItemAmount = 'any_amount',
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
        what_to_check: ItemProperty | Missing = MISSING,
        where_to_check: ItemLocation | Missing = MISSING,
        required_amount: ItemAmount | Missing = MISSING,
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


@final
class IsItem(Condition):
    htsw_meta = ConditionMeta(
        htsw_name='IS_ITEM',
        limit=20,
        reads=frozenset((Resource.INVENTORY,)),
        display_name='Is Item',
        scoped_events=(
            'player_drop_item',
            'player_pick_up_item',
            'player_change_held_item',
        ),
    )

    item: Item

    def __init__(
        self,
        item: Item,
    ) -> None:
        self.item = item

    def into_htsl_raw(self) -> str:
        name = item_action_reference(self.item)
        return f'isItem {self.inline_quoted(name)}'

    def referenced_importables(self) -> list[tuple[str, str]]:
        return item_referenced_importables(self.item)

    def cloned(
        self,
        *,
        item: Item | Missing = MISSING,
        inverted: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'item': item,
                'inverted': inverted,
            },
        )
