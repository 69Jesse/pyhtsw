from typing import Self, cast, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.expression.expression import Expression
from pyhtsw.location import Location, resolve_location
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource
from pyhtsw.types import ALL_LOCATIONS

__all__ = (
    'TeleportPlayerExpression',
    'teleport_player',
)


@final
class TeleportPlayerExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='TELEPORT',
        limit=5,
        effects=Effects.of(reads=(Resource.POSITION,), writes=(Resource.POSITION,)),
        display_name='Teleport Player',
        forbidden_events=('Player Quit',),
    )

    coordinates: str | None
    location: ALL_LOCATIONS
    prevent_teleport_inside_block: bool

    def __init__(
        self,
        coordinates: str | None = None,
        location: ALL_LOCATIONS = 'custom_coordinates',
        prevent_teleport_inside_block: bool = False,
    ) -> None:
        self.coordinates = coordinates
        self.location = location
        self.prevent_teleport_inside_block = prevent_teleport_inside_block

    def into_htsl(self) -> str:
        line = f'tp {self.inline_quoted(self.location)}'
        if self.location == 'custom_coordinates' and self.coordinates is not None:
            line += f' {self.inline_quoted(self.coordinates)}'
        else:
            line += f' {self.inline_quoted("~ ~ ~")}'
        line += f' {self.inline(self.prevent_teleport_inside_block)}'
        return line

    def cloned(
        self,
        *,
        coordinates: str | None | Missing = MISSING,
        location: ALL_LOCATIONS | Missing = MISSING,
        prevent_teleport_inside_block: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'coordinates': coordinates,
                'location': location,
                'prevent_teleport_inside_block': prevent_teleport_inside_block,
            },
        )


def teleport_player(
    location: Location,
    prevent_teleport_inside_block: bool = False,
) -> None:
    keyword, coordinates = resolve_location(location)
    TeleportPlayerExpression(
        coordinates=coordinates,
        location=cast(ALL_LOCATIONS, keyword),
        prevent_teleport_inside_block=prevent_teleport_inside_block,
    ).write()
