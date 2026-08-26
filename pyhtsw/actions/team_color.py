import re
from typing import final

from pyhtsw.execute.backend_type import BackendType
from pyhtsw.internal_type import InternalType
from pyhtsw.placeholders import PlaceholderCheckable
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

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
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.TEAM,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.team.color%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''


TeamColor = TeamColorPlaceholder()
