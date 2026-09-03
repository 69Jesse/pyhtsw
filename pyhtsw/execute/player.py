from typing import TYPE_CHECKING, Literal, overload

from pyhtsw.checkable import Checkable
from pyhtsw.execute.backend_type import BackendType
from pyhtsw.expression.housing_type import HousingType

if TYPE_CHECKING:
    from pyhtsw.execute.house import EmulatedHouse

__all__ = ('EmulatedPlayer',)


class EmulatedPlayer:
    """An emulated player inside an `EmulatedHouse`.

    Player-scoped state (`var` / `%player.…%`) lives in `mapping`; everything
    else (`globalvar`, …) lives on the house and is shared. Every read/write
    method just forwards to the owning house bound to `self`, so there is a
    single source of truth for the get/put/substitute logic.
    """

    name: str | None
    house: 'EmulatedHouse | None'
    mapping: dict[tuple[object, ...], BackendType]
    functions_on_cooldown_for_ticks: dict[str, int]

    def __init__(self, name: str | None = None) -> None:
        self.name = name
        self.house = None
        self.mapping = {}
        self.functions_on_cooldown_for_ticks = {}

    def _house(self) -> 'EmulatedHouse':
        if self.house is None:
            raise RuntimeError(
                'This EmulatedPlayer is not attached to an EmulatedHouse yet. '
                'Pass it via EmulatedHouse(players=[...]) or house.add_player(...).',
            )
        return self.house

    def put(
        self,
        key: Checkable,
        value: HousingType | BackendType,
        *,
        ignore_warning: bool = False,
    ) -> None:
        self._house().put(key, value, ignore_warning=ignore_warning, player=self)

    @overload
    def get(
        self,
        key: Checkable | HousingType,
        *,
        cast: bool = True,
        output: Literal['regular'] = ...,
    ) -> HousingType: ...

    @overload
    def get(
        self,
        key: Checkable | HousingType,
        *,
        cast: bool = True,
        output: Literal['backend'],
    ) -> BackendType: ...

    @overload
    def get(
        self,
        key: Checkable | HousingType,
        *,
        cast: bool = True,
        output: Literal['string'],
    ) -> str: ...

    def get(
        self,
        key: Checkable | HousingType,
        *,
        cast: bool = True,
        output: Literal['regular', 'backend', 'string'] = 'regular',
    ) -> HousingType | BackendType | str:
        return self._house().get(key, cast=cast, output=output, player=self)

    def get_raw(
        self,
        key: Checkable,
        *,
        default: HousingType | None = None,
    ) -> HousingType:
        return self._house().get_raw(key, default=default, player=self)

    def pop(self, key: Checkable) -> None:
        self._house().pop(key, player=self)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.name!r})'
