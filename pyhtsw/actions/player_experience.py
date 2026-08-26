import re
from typing import final

from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

from ..execute.backend_type import BackendType, JavaLong
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = (
    'PlayerExperiencePlaceholder',
    'PlayerExperience',
)


@final
class PlayerExperiencePlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.experience%')),
    pattern_factory=lambda _: PlayerExperience,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.EXPERIENCE,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.experience%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(0)


PlayerExperience = PlayerExperiencePlaceholder()
