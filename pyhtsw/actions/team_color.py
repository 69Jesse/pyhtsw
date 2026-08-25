import re
from typing import final

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = (
    'TeamColorPlaceholder',
    'TeamColor',
)


@final
class TeamColorPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.team.color%')),
    pattern_factory=lambda _: TeamColor,
):
    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.team.color%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''


TeamColor = TeamColorPlaceholder()
