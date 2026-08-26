import re
from typing import final

import numpy as np

from pyhtsw.execute.backend_type import BackendType
from pyhtsw.internal_type import InternalType
from pyhtsw.placeholders import PlaceholderCheckable
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

__all__ = (
    'PlayerPositionPitchPlaceholder',
    'PlayerPositionPitch',
)


@final
class PlayerPositionPitchPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.pos.pitch%')),
    pattern_factory=lambda _: PlayerPositionPitch,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.POSITION,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.pos.pitch%',
            constant_internal_type=InternalType.DOUBLE,
        )

    def get_backend_value(self) -> BackendType:
        return np.float64(0)


PlayerPositionPitch = PlayerPositionPitchPlaceholder()
