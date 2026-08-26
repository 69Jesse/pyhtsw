from typing import ClassVar, Self, final

from pyhtsw.clone import MISSING, Missing, clone_with

from ..expression.condition.condition import Condition
from .region import Region

__all__ = ('WithinRegion',)


def _region_name(region: 'Region | str') -> str:
    if isinstance(region, str):
        return region
    if isinstance(region, Region):
        return region.name
    raise TypeError(f'Expected a Region or str, got {region!r}')


@final
class WithinRegion(Condition):
    name: str
    __clone_map__: ClassVar[dict[str, str]] = {'region': 'name'}

    def __init__(self, region: 'Region | str') -> None:
        self.name = _region_name(region)

    def into_htsl_raw(self) -> str:
        return f'inRegion {self.inline_quoted(self.name)}'

    def cloned(
        self,
        *,
        region: 'Region | str | Missing' = MISSING,
        inverted: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'region': region,
                'inverted': inverted,
            },
        )

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, WithinRegion):
            return False
        return self.name == other.name

    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}<region={self.name!r} inverted={self.inverted}>'
        )
