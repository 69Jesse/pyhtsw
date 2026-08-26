import re
from typing import final

from pyhtsw.execute.backend_type import BackendType, JavaLong
from pyhtsw.internal_type import InternalType
from pyhtsw.placeholders import PlaceholderCheckable
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

__all__ = (
    'GroupPriorityPlaceholder',
    'GroupPriority',
)


@final
class GroupPriorityPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.group.priority%')),
    pattern_factory=lambda _: GroupPriority,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.GROUP,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.group.priority%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(0)


GroupPriority = GroupPriorityPlaceholder()
