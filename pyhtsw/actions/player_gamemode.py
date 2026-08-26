import re
from typing import final

from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = (
    'PlayerGamemodePlaceholder',
    'PlayerGamemode',
)


@final
class PlayerGamemodePlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.gamemode%')),
    pattern_factory=lambda _: PlayerGamemode,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.GAMEMODE,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.gamemode%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''


PlayerGamemode = PlayerGamemodePlaceholder()
