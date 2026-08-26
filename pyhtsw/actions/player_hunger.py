import re
from typing import final

from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

from ..execute.backend_type import BackendType, JavaLong
from ..internal_type import InternalType
from ..placeholders import PlaceholderEditable

__all__ = (
    'PlayerHungerPlaceholder',
    'PlayerHunger',
)


@final
class PlayerHungerPlaceholder(
    PlaceholderEditable,
    pattern=re.compile(re.escape('%player.hunger%')),
    pattern_factory=lambda _: PlayerHunger,
):
    htsw_meta = ActionMeta(
        htsw_name='CHANGE_HUNGER',
        limit=5,
        effects=Effects.of(reads=(Resource.HUNGER,)),
        display_name='Change Hunger Level',
        forbidden_events=('Player Quit',),
    )

    def __init__(self) -> None:
        super().__init__(
            assignment_lhs='hunger',
            placeholder='%player.hunger%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(0)


PlayerHunger = PlayerHungerPlaceholder()
