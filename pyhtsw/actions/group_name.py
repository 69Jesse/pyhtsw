import re
from typing import final

from pyhtsw.execute.backend_type import BackendType
from pyhtsw.internal_type import InternalType
from pyhtsw.placeholders import PlaceholderCheckable
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

__all__ = (
    'GroupNamePlaceholder',
    'GroupName',
)


@final
class GroupNamePlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.group.name%')),
    pattern_factory=lambda _: GroupName,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.GROUP,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.group.name%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''


GroupName = GroupNamePlaceholder()
