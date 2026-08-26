from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.compiler.registry import ActionMeta
from pyhtsw.compiler.schedule import Effects, Resource
from pyhtsw.declarations.item import (
    Enchantment,
    Item,
    item_action_reference,
    item_referenced_importables,
)
from pyhtsw.expression.expression import Expression
from pyhtsw.location import Location, resolve_location
from pyhtsw.types import (
    _INVENTORY_SLOTS_PRETTY_NAME_MAPPING,
    ALL_ENCHANTMENTS,
    INVENTORY_SLOTS,
)

__all__ = (
    'Layout',
    'GiveItemExpression',
    'give_item',
    'RemoveItemExpression',
    'remove_item',
    'DropItemExpression',
    'drop_item',
    'ConsumeItemExpression',
    'consume_item',
    'EnchantHeldItemExpression',
    'enchant_held_item',
    'ApplyInventoryLayoutExpression',
    'apply_inventory_layout',
    'ResetInventoryExpression',
    'reset_inventory',
)


class Layout:
    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Layout):
            return NotImplemented
        return self.name == other.name


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


@final
class DropItemExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='DROP_ITEM',
        limit=5,
        effects=Effects.of(
            reads=(
                Resource.INVENTORY,
                Resource.POSITION,
            ),
            writes=(
                Resource.INVENTORY,
                Resource.WORLD,
            ),
        ),
        display_name='Drop Item',
        forbidden_events=('Player Quit',),
    )

    item: Item
    location: str
    coordinates: str | None
    drop_naturally: bool
    disable_item_merging: bool
    prioritize_player: bool
    fallback_to_inventory: bool
    despawn_duration_ticks: int
    pickup_delay_ticks: int

    def __init__(
        self,
        item: Item,
        location: str,
        coordinates: str | None,
        drop_naturally: bool = False,
        disable_item_merging: bool = False,
        prioritize_player: bool = False,
        fallback_to_inventory: bool = False,
        despawn_duration_ticks: int = 6000,
        pickup_delay_ticks: int = 10,
    ) -> None:
        self.item = item
        self.location = location
        self.coordinates = coordinates
        self.drop_naturally = drop_naturally
        self.disable_item_merging = disable_item_merging
        self.prioritize_player = prioritize_player
        self.fallback_to_inventory = fallback_to_inventory
        self.despawn_duration_ticks = despawn_duration_ticks
        self.pickup_delay_ticks = pickup_delay_ticks

    def into_htsl(self) -> str:
        name = item_action_reference(self.item)
        coordinates = self.coordinates if self.coordinates is not None else '~ ~ ~'
        return (
            f'dropItem {self.inline_quoted(name)}'
            f' {self.inline_quoted(self.location)} {self.inline_quoted(coordinates)}'
            f' {self.inline(self.drop_naturally)} {self.inline(self.disable_item_merging)}'
            f' {self.inline(self.prioritize_player)} {self.inline(self.fallback_to_inventory)}'
            f' {self.inline(self.despawn_duration_ticks)} {self.inline(self.pickup_delay_ticks)}'
        )

    def referenced_importables(self) -> list[tuple[str, str]]:
        return item_referenced_importables(self.item)

    def cloned(
        self,
        *,
        item: Item | Missing = MISSING,
        location: str | Missing = MISSING,
        coordinates: str | None | Missing = MISSING,
        drop_naturally: bool | Missing = MISSING,
        disable_item_merging: bool | Missing = MISSING,
        prioritize_player: bool | Missing = MISSING,
        fallback_to_inventory: bool | Missing = MISSING,
        despawn_duration_ticks: int | Missing = MISSING,
        pickup_delay_ticks: int | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'item': item,
                'location': location,
                'coordinates': coordinates,
                'drop_naturally': drop_naturally,
                'disable_item_merging': disable_item_merging,
                'prioritize_player': prioritize_player,
                'fallback_to_inventory': fallback_to_inventory,
                'despawn_duration_ticks': despawn_duration_ticks,
                'pickup_delay_ticks': pickup_delay_ticks,
            },
        )


def drop_item(
    item: Item,
    location: Location,
    drop_naturally: bool = False,
    disable_item_merging: bool = False,
    prioritize_player: bool = False,
    fallback_to_inventory: bool = False,
    despawn_duration_ticks: int = 6000,
    pickup_delay_ticks: int = 10,
) -> None:
    keyword, coordinates = resolve_location(location)
    DropItemExpression(
        item=item,
        location=keyword,
        coordinates=coordinates,
        drop_naturally=drop_naturally,
        disable_item_merging=disable_item_merging,
        prioritize_player=prioritize_player,
        fallback_to_inventory=fallback_to_inventory,
        despawn_duration_ticks=despawn_duration_ticks,
        pickup_delay_ticks=pickup_delay_ticks,
    ).write()


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


@final
class EnchantHeldItemExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='ENCHANT_HELD_ITEM',
        limit=24,
        effects=Effects.of(reads=(Resource.INVENTORY,), writes=(Resource.INVENTORY,)),
        display_name='Enchant Held Item',
        forbidden_events=('Player Quit',),
    )

    enchantment_name: str
    level: int

    def __init__(self, enchantment_name: str, level: int) -> None:
        self.enchantment_name = enchantment_name
        self.level = level

    def into_htsl(self) -> str:
        return f'enchant {self.inline_quoted(self.enchantment_name)} {self.inline(self.level)}'

    def cloned(
        self,
        *,
        enchantment_name: str | Missing = MISSING,
        level: int | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'enchantment_name': enchantment_name,
                'level': level,
            },
        )


def enchant_held_item(
    enchantment: ALL_ENCHANTMENTS | Enchantment,
    level: int | None = None,
) -> None:
    if isinstance(enchantment, Enchantment):
        name = enchantment.name
        if level is None:
            level = enchantment.level
    else:
        name = enchantment
    if level is None:
        level = 1
    EnchantHeldItemExpression(enchantment_name=name, level=level).write()


@final
class ApplyInventoryLayoutExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='APPLY_INVENTORY_LAYOUT',
        limit=5,
        effects=Effects.of(writes=(Resource.INVENTORY,)),
        display_name='Apply Inventory Layout',
        forbidden_events=('Player Quit',),
    )

    layout: Layout

    def __init__(self, layout: Layout) -> None:
        self.layout = layout

    def into_htsl(self) -> str:
        return f'applyLayout {self.inline_quoted(self.layout.name)}'

    def cloned(
        self,
        *,
        layout: Layout | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'layout': layout,
            },
        )


def apply_inventory_layout(layout: Layout | str) -> None:
    layout = layout if isinstance(layout, Layout) else Layout(layout)
    ApplyInventoryLayoutExpression(layout=layout).write()


@final
class ResetInventoryExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='RESET_INVENTORY',
        limit=1,
        effects=Effects.of(writes=(Resource.INVENTORY,)),
        display_name='Reset Inventory',
        forbidden_events=('Player Quit',),
    )

    def into_htsl(self) -> str:
        return 'resetInventory'


def reset_inventory() -> None:
    ResetInventoryExpression().write()
