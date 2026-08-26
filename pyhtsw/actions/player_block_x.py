import re
from typing import final

from pyhtsw.execute.backend_type import BackendType, JavaLong
from pyhtsw.internal_type import InternalType
from pyhtsw.placeholders import PlaceholderCheckable
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

__all__ = (
    'PlayerBlockXPlaceholder',
    'PlayerBlockX',
)


@final
class PlayerBlockXPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.block.x%')),
    pattern_factory=lambda _: PlayerBlockX,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.POSITION,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.block.x%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(0)


PlayerBlockX = PlayerBlockXPlaceholder()
