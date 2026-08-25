from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with

from ..expression.expression import Expression
from ..location import Location, resolve_location
from .item import Item, item_action_reference, item_referenced_importables

__all__ = (
    'DropItemExpression',
    'drop_item',
)


@final
class DropItemExpression(Expression):
    item: Item | type[Item]
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
        item: Item | type[Item],
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
        item: Item | type[Item] | Missing = MISSING,
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

    def equals(self, other: object) -> bool:
        if not isinstance(other, DropItemExpression):
            return False
        return (
            self.item == other.item
            and self.location == other.location
            and self.coordinates == other.coordinates
            and self.drop_naturally == other.drop_naturally
            and self.disable_item_merging == other.disable_item_merging
            and self.prioritize_player == other.prioritize_player
            and self.fallback_to_inventory == other.fallback_to_inventory
            and self.despawn_duration_ticks == other.despawn_duration_ticks
            and self.pickup_delay_ticks == other.pickup_delay_ticks
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.item} at={self.location} {self.coordinates}>'


def drop_item(
    item: Item | type[Item],
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
