import re
from typing import final

import numpy as np

from pyhtsw.execute.backend_type import BackendType
from pyhtsw.internal_type import InternalType
from pyhtsw.placeholders import PlaceholderEditable
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

__all__ = (
    'PlayerMaxHealthPlaceholder',
    'PlayerMaxHealth',
)


@final
class PlayerMaxHealthPlaceholder(
    PlaceholderEditable,
    pattern=re.compile(re.escape('%player.maxhealth%')),
    pattern_factory=lambda _: PlayerMaxHealth,
):
    htsw_meta = ActionMeta(
        htsw_name='CHANGE_MAX_HEALTH',
        limit=5,
        effects=Effects.of(reads=(Resource.MAX_HEALTH,)),
        display_name='Change Max Health',
        forbidden_events=('Player Quit',),
    )

    def __init__(self) -> None:
        super().__init__(
            assignment_lhs='maxHealth',
            placeholder='%player.maxhealth%',
            constant_internal_type=InternalType.DOUBLE,
        )

    def get_backend_value(self) -> BackendType:
        return np.float64(0)


PlayerMaxHealth = PlayerMaxHealthPlaceholder()
