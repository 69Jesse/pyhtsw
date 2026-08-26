import re
from typing import final

from pyhtsw.execute.backend_type import BackendType
from pyhtsw.internal_type import InternalType
from pyhtsw.placeholders import PlaceholderCheckable
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

__all__ = (
    'GroupColorPlaceholder',
    'GroupColor',
)


@final
class GroupColorPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.group.color%')),
    pattern_factory=lambda _: GroupColor,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.GROUP,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.group.color%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''


GroupColor = GroupColorPlaceholder()
