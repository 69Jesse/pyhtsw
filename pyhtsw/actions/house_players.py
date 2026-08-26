import re
from typing import final

from pyhtsw.execute.backend_type import BackendType, JavaLong
from pyhtsw.internal_type import InternalType
from pyhtsw.placeholders import PlaceholderCheckable
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects

__all__ = (
    'HousePlayersPlaceholder',
    'HousePlayers',
)


@final
class HousePlayersPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%house.players%')),
    pattern_factory=lambda _: HousePlayers,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%house.players%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(0)


HousePlayers = HousePlayersPlaceholder()
