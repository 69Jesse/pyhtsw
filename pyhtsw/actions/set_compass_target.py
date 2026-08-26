from typing import Self, cast, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

from ..expression.expression import Expression
from ..location import Location, resolve_location
from ..types import ALL_LOCATIONS

__all__ = (
    'SetCompassTargetExpression',
    'set_compass_target',
)


@final
class SetCompassTargetExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='SET_COMPASS_TARGET',
        limit=5,
        effects=Effects.of(writes=(Resource.COMPASS,)),
        display_name='Set Compass Target',
        forbidden_events=('Player Quit',),
    )

    coordinates: str | None
    location: ALL_LOCATIONS

    def __init__(
        self,
        coordinates: str | None = None,
        location: ALL_LOCATIONS = 'custom_coordinates',
    ) -> None:
        self.coordinates = coordinates
        self.location = location

    def into_htsl(self) -> str:
        line = f'compassTarget {self.inline_quoted(self.location)}'
        if self.location == 'custom_coordinates' and self.coordinates is not None:
            line += f' {self.inline_quoted(self.coordinates)}'
        return line

    def cloned(
        self,
        *,
        coordinates: str | None | Missing = MISSING,
        location: ALL_LOCATIONS | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'coordinates': coordinates,
                'location': location,
            },
        )


def set_compass_target(location: Location) -> None:
    keyword, coordinates = resolve_location(location)
    SetCompassTargetExpression(
        coordinates=coordinates,
        location=cast(ALL_LOCATIONS, keyword),
    ).write()
