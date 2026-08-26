import re
from typing import final

import numpy as np

from pyhtsw.execute.backend_type import BackendType
from pyhtsw.internal_type import InternalType
from pyhtsw.placeholders import PlaceholderEditable
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

__all__ = (
    'PlayerHealthPlaceholder',
    'PlayerHealth',
)


@final
class PlayerHealthPlaceholder(
    PlaceholderEditable,
    pattern=re.compile(re.escape('%player.health%')),
    pattern_factory=lambda _: PlayerHealth,
):
    htsw_meta = ActionMeta(
        htsw_name='CHANGE_HEALTH',
        limit=5,
        effects=Effects.of(reads=(Resource.HEALTH,)),
        display_name='Change Health',
        forbidden_events=('Player Quit',),
    )

    def __init__(self) -> None:
        super().__init__(
            assignment_lhs='changeHealth',
            condition_lhs='health',
            placeholder='%player.health%',
            constant_internal_type=InternalType.DOUBLE,
        )

    def get_backend_value(self) -> BackendType:
        return np.float64(0)


PlayerHealth = PlayerHealthPlaceholder()
