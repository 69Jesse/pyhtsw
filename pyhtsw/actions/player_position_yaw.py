import re
from typing import final

import numpy as np

from pyhtsw.execute.backend_type import BackendType
from pyhtsw.internal_type import InternalType
from pyhtsw.placeholders import PlaceholderCheckable
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

__all__ = (
    'PlayerPositionYawPlaceholder',
    'PlayerPositionYaw',
)


@final
class PlayerPositionYawPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.pos.yaw%')),
    pattern_factory=lambda _: PlayerPositionYaw,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.POSITION,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.pos.yaw%',
            constant_internal_type=InternalType.DOUBLE,
        )

    def get_backend_value(self) -> BackendType:
        return np.float64(0)


PlayerPositionYaw = PlayerPositionYawPlaceholder()
