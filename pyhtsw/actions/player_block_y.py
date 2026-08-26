import re
from typing import final

from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

from ..execute.backend_type import BackendType, JavaLong
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = (
    'PlayerBlockYPlaceholder',
    'PlayerBlockY',
)


@final
class PlayerBlockYPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.block.y%')),
    pattern_factory=lambda _: PlayerBlockY,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.POSITION,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.block.y%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(0)


PlayerBlockY = PlayerBlockYPlaceholder()
