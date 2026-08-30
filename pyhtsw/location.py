from collections.abc import Generator
from typing import TYPE_CHECKING, ClassVar

from pyhtsw.base_object import BaseObject
from pyhtsw.checkable import Checkable
from pyhtsw.directives.no_fallback_values import NoFallbackValues
from pyhtsw.expression.housing_type import HousingType
from pyhtsw.generated.enums import LocationName

if TYPE_CHECKING:
    from pyhtsw.stats.stat import Stat

__all__ = (
    'Location',
    'LocationName',
    'ensure_location',
)

Coordish = Checkable | HousingType | float | int

_COORDINATE_FIELDS = ('x', 'y', 'z', 'yaw', 'pitch')


def _render_coordinate(value: Coordish) -> str:
    # `resolved_inside_string`, never `str`: a held `TemporaryStat` defers when
    # stringified, and a derived render must not register anything.
    if isinstance(value, Checkable):
        return value.resolved_inside_string()
    return str(value)


class Location:
    """Base for the housing location types. Construct via the factory
    classmethods (``Location.custom`` / ``Location.house_spawn`` / ... ); the
    bare ``Location`` itself is never a valid value."""

    keyword: ClassVar[LocationName]

    def into_htsl(self) -> str:
        return BaseObject.inline_quoted(type(self).keyword)

    def coordinate_fields(self) -> tuple[str, ...]:
        """The attributes holding this location's coordinate operands. They are
        the only state a location carries: everything the compiler substitutes
        into, scans or renders is derived from them."""
        return ()

    def coordinate_values(self) -> tuple[Coordish, ...]:
        return tuple(getattr(self, name) for name in self.coordinate_fields())

    def iter_referenced_stats(self) -> 'Generator[Stat]':
        from pyhtsw.expression.expression import Expression
        from pyhtsw.stats.stat import Stat

        for value in self.coordinate_values():
            if isinstance(value, Stat):
                yield value
            elif isinstance(value, Expression):
                for expr in value.walk_expressions():
                    for stat, _ in expr.get_all_stats_used():
                        yield stat

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
    keyword = 'house_spawn_location'


class CurrentLocation(Location):
    keyword = 'current_location'


class InvokersLocation(Location):
    keyword = 'invokers_location'


class CustomLocation(Location):
    keyword = 'custom_coordinates'

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

    def coordinate_fields(self) -> tuple[str, ...]:
        return tuple(
            name for name in _COORDINATE_FIELDS if getattr(self, name) is not None
        )

    @property
    def coordinates(self) -> str:
        # Yaw and pitch travel together: one given means the other renders as 0.
        parts: list[Coordish] = [self.x, self.y, self.z]
        if self.yaw is not None or self.pitch is not None:
            parts.append(self.yaw if self.yaw is not None else 0)
            parts.append(self.pitch if self.pitch is not None else 0)
        with NoFallbackValues():
            return ' '.join(_render_coordinate(part) for part in parts)

    def into_htsl(self) -> str:
        return f'{super().into_htsl()} {BaseObject.inline_quoted(self.coordinates)}'

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
