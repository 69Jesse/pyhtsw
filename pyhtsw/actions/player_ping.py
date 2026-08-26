import re
from typing import final

from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects

from ..execute.backend_type import BackendType, JavaLong
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = (
    'PlayerPingPlaceholder',
    'PlayerPing',
)


@final
class PlayerPingPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.ping%')),
    pattern_factory=lambda _: PlayerPing,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.ping%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(0)


PlayerPing = PlayerPingPlaceholder()
