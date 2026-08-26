import re
from typing import final

from pyhtsw.compiler.registry import ActionMeta
from pyhtsw.compiler.schedule import Effects, Resource
from pyhtsw.execute.backend_type import BackendType, JavaLong
from pyhtsw.internal_type import InternalType
from pyhtsw.placeholders.base import PlaceholderCheckable

__all__ = (
    'GroupColorPlaceholder',
    'GroupColor',
    'GroupNamePlaceholder',
    'GroupName',
    'GroupPriorityPlaceholder',
    'GroupPriority',
    'GroupTagPlaceholder',
    'GroupTag',
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


@final
class GroupTagPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.group.tag%')),
    pattern_factory=lambda _: GroupTag,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.GROUP,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.group.tag%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''


GroupTag = GroupTagPlaceholder()
