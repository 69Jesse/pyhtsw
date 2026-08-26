from typing import Self, cast, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

from ..checkable import Checkable
from ..expression.expression import Expression
from ..location import Location, resolve_location
from ..types import ALL_LOCATIONS

__all__ = (
    'LaunchToTargetExpression',
    'launch_to_target',
)


@final
class LaunchToTargetExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='LAUNCH',
        limit=5,
        effects=Effects.of(reads=(Resource.POSITION,), writes=(Resource.VELOCITY,)),
        display_name='Launch to Target',
        forbidden_events=('Player Quit',),
    )

    coordinates: str | None
    location: ALL_LOCATIONS
    strength: Checkable | int

    def __init__(
        self,
        coordinates: str | None = None,
        location: ALL_LOCATIONS = 'custom_coordinates',
        strength: Checkable | int = 2,
    ) -> None:
        self.coordinates = coordinates
        self.location = location
        self.strength = strength

    def into_htsl(self) -> str:
        line = f'launchTarget {self.inline_quoted(self.location)}'
        if self.location == 'custom_coordinates' and self.coordinates is not None:
            line += f' {self.inline_quoted(self.coordinates)}'
        else:
            line += f' {self.inline_quoted("~ ~ ~")}'
        line += f' {self.inline(self.strength)}'
        return line

    def cloned(
        self,
        *,
        coordinates: str | None | Missing = MISSING,
        location: ALL_LOCATIONS | Missing = MISSING,
        strength: Checkable | int | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'coordinates': coordinates,
                'location': location,
                'strength': strength,
            },
        )


def launch_to_target(
    location: Location,
    strength: Checkable | int = 2,
) -> None:
    keyword, coordinates = resolve_location(location)
    LaunchToTargetExpression(
        coordinates=coordinates,
        location=cast(ALL_LOCATIONS, keyword),
        strength=strength,
    ).write()
