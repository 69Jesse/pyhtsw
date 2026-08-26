from typing import Self, final

from pyhtsw.actions.item import Item, item_action_reference, item_referenced_importables
from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.expression.expression import Expression
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource
from pyhtsw.types import _INVENTORY_SLOTS_PRETTY_NAME_MAPPING, INVENTORY_SLOTS

__all__ = (
    'GiveItemExpression',
    'give_item',
)


@final
class GiveItemExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='GIVE_ITEM',
        limit=40,
        effects=Effects.of(reads=(Resource.INVENTORY,), writes=(Resource.INVENTORY,)),
        display_name='Give Item',
        forbidden_events=('Player Quit',),
    )

    item: Item
    allow_multiple: bool
    inventory_slot: str | int
    replace_existing_item: bool

    def __init__(
        self,
        item: Item,
        allow_multiple: bool = False,
        inventory_slot: str | int = 'first_slot',
        replace_existing_item: bool = False,
    ) -> None:
        self.item = item
        self.allow_multiple = allow_multiple
        self.inventory_slot = inventory_slot
        self.replace_existing_item = replace_existing_item

    def into_htsl(self) -> str:
        name = item_action_reference(self.item)
        # Numeric slots are emitted bare (htsw accepts -1..39); named slots
        # (e.g. "First Available Slot", "Hand Slot") are quoted.
        slot = (
            self.inline(self.inventory_slot)
            if isinstance(self.inventory_slot, int)
            else self.inline_quoted(self.inventory_slot)
        )
        return (
            f'giveItem {self.inline_quoted(name)} {self.inline(self.allow_multiple)}'
            f' {slot} {self.inline(self.replace_existing_item)}'
        )

    def referenced_importables(self) -> list[tuple[str, str]]:
        return item_referenced_importables(self.item)

    def cloned(
        self,
        *,
        item: Item | Missing = MISSING,
        allow_multiple: bool | Missing = MISSING,
        inventory_slot: str | int | Missing = MISSING,
        replace_existing_item: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'item': item,
                'allow_multiple': allow_multiple,
                'inventory_slot': inventory_slot,
                'replace_existing_item': replace_existing_item,
            },
        )


def give_item(
    item: Item,
    allow_multiple: bool = False,
    inventory_slot: INVENTORY_SLOTS = 'first_slot',
    replace_existing_item: bool = False,
) -> None:
    inventory_slot = _INVENTORY_SLOTS_PRETTY_NAME_MAPPING.get(
        inventory_slot,
        inventory_slot,
    )
    GiveItemExpression(
        item=item,
        allow_multiple=allow_multiple,
        inventory_slot=inventory_slot,
        replace_existing_item=replace_existing_item,
    ).write()
