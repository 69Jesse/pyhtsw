import re
from typing import final

from pyhtsw.execute.backend_type import BackendType
from pyhtsw.internal_type import InternalType
from pyhtsw.placeholders import PlaceholderCheckable
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects

__all__ = (
    'PlayerVersionPlaceholder',
    'PlayerVersion',
)


@final
class PlayerVersionPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.version%')),
    pattern_factory=lambda _: PlayerVersion,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.version%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''


PlayerVersion = PlayerVersionPlaceholder()
