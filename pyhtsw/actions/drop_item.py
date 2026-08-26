from typing import Self, final

from pyhtsw.actions.item import Item, item_action_reference, item_referenced_importables
from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.expression.expression import Expression
from pyhtsw.location import Location, resolve_location
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

__all__ = (
    'DropItemExpression',
    'drop_item',
)


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
