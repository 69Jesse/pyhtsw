import re
from typing import final

from pyhtsw.execute.backend_type import BackendType
from pyhtsw.internal_type import InternalType
from pyhtsw.placeholders import PlaceholderCheckable
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

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
