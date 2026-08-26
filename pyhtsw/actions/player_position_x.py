import re
from typing import final

import numpy as np

from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = (
    'PlayerPositionXPlaceholder',
    'PlayerPositionX',
)


@final
class PlayerPositionXPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.pos.x%')),
    pattern_factory=lambda _: PlayerPositionX,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.POSITION,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.pos.x%',
            constant_internal_type=InternalType.DOUBLE,
        )

    def get_backend_value(self) -> BackendType:
        return np.float64(0)


PlayerPositionX = PlayerPositionXPlaceholder()
