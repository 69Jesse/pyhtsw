import re
from typing import final

from pyhtsw.execute.backend_type import BackendType
from pyhtsw.internal_type import InternalType
from pyhtsw.placeholders import PlaceholderCheckable
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects

__all__ = (
    'PlayerNamePlaceholder',
    'PlayerName',
)


@final
class PlayerNamePlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.name%')),
    pattern_factory=lambda _: PlayerName,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.name%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return 'Rfind'


PlayerName = PlayerNamePlaceholder()
