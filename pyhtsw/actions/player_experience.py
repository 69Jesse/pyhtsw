import re
from typing import final

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
    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.experience%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(0)


PlayerExperience = PlayerExperiencePlaceholder()
