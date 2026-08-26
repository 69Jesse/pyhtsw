from typing import ClassVar, Literal

from pyhtsw.base_object import BaseObject
from pyhtsw.checkable import Checkable
from pyhtsw.directives.no_fallback_values import NoFallbackValues
from pyhtsw.expression.housing_type import HousingType

LocationName = Literal[
    'house_spawn',
    'current_location',
    'invokers_location',
    'custom_coordinates',
]

__all__ = (
    'Location',
    'LocationName',
    'ensure_location',
)

Coordish = Checkable | HousingType | float | int


class Location:
    """Base for the housing location types. Construct via the factory
    classmethods (``Location.custom`` / ``Location.house_spawn`` / ... ); the
    bare ``Location`` itself is never a valid value."""

    keyword: ClassVar[LocationName]

    def render(self) -> tuple[LocationName, str | None]:
        return type(self).keyword, None

    def replace_deferred_text(self, text: str) -> None:
        raise TypeError(f'{type(self).__name__} carries no coordinate text')

    def __eq__(self, other: object) -> bool:
        return type(other) is type(self)

    def __hash__(self) -> int:
        return hash(type(self))

    def __repr__(self) -> str:
        return f'{type(self).__name__}<{type(self).keyword}>'

    @staticmethod
    def custom(
        x: Coordish,
        y: Coordish,
        z: Coordish,
        yaw: Coordish | None = None,
        pitch: Coordish | None = None,
    ) -> 'CustomLocation':
        return CustomLocation(x, y, z, yaw, pitch)

    @staticmethod
    def house_spawn() -> 'HouseSpawnLocation':
        return HouseSpawnLocation()

    @staticmethod
    def invokers() -> 'InvokersLocation':
        return InvokersLocation()

    @staticmethod
    def current() -> 'CurrentLocation':
        return CurrentLocation()


class HouseSpawnLocation(Location):
    keyword = 'house_spawn'


class CurrentLocation(Location):
    keyword = 'current_location'


class InvokersLocation(Location):
    keyword = 'invokers_location'


class CustomLocation(Location):
    keyword = 'custom_coordinates'

    _coordinates: str | None

    def __init__(
        self,
        x: Coordish,
        y: Coordish,
        z: Coordish,
        yaw: Coordish | None = None,
        pitch: Coordish | None = None,
    ) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.yaw = yaw
        self.pitch = pitch
        self._coordinates = None

    def render(self) -> tuple[LocationName, str | None]:
        # Rendered once and cached: stringifying a computed coordinate registers
        # its deferred entry, and clones share this object, so re-rendering
        # would register (and materialize) the same computation twice.
        if self._coordinates is None:
            parts: list[Coordish] = [self.x, self.y, self.z]
            if self.yaw is not None or self.pitch is not None:
                parts.append(self.yaw if self.yaw is not None else 0)
                parts.append(self.pitch if self.pitch is not None else 0)
            with NoFallbackValues():
                self._coordinates = ' '.join(str(part) for part in parts)
        return type(self).keyword, self._coordinates

    def replace_deferred_text(self, text: str) -> None:
        self._coordinates = text

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return NotImplemented
        assert isinstance(other, CustomLocation)
        return all(
            BaseObject.equals_or_eq(getattr(self, field), getattr(other, field))
            for field in ('x', 'y', 'z', 'yaw', 'pitch')
        )

    __hash__ = None  # type: ignore[assignment]

    def __repr__(self) -> str:
        return (
            f'{type(self).__name__}<{self.x} {self.y} {self.z}'
            f'{"" if self.yaw is None else f" {self.yaw}"}'
            f'{"" if self.pitch is None else f" {self.pitch}"}>'
        )


def ensure_location(location: Location) -> Location:
    if not isinstance(location, Location) or type(location) is Location:
        raise TypeError(
            'Expected a concrete Location, e.g. Location.custom(x, y, z), '
            'Location.house_spawn(), Location.invokers() or Location.current().',
        )
    return location
