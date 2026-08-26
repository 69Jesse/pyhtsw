from typing import Self, final

from pyhtsw.actions.group import Group
from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.expression.condition.condition import Condition
from pyhtsw.registry import ConditionMeta
from pyhtsw.schedule import Resource

__all__ = ('RequiredGroup',)


@final
class RequiredGroup(Condition):
    htsw_meta = ConditionMeta(
        htsw_name='REQUIRE_GROUP',
        limit=20,
        reads=frozenset((Resource.GROUP,)),
    )

    group: Group
    include_higher_groups: bool

    def __init__(
        self,
        group: Group | str,
        include_higher_groups: bool = False,
    ) -> None:
        self.group = group if isinstance(group, Group) else Group(group)
        self.include_higher_groups = include_higher_groups

    def into_htsl_raw(self) -> str:
        return f'hasGroup {self.inline_quoted(self.group.name)} {self.inline(self.include_higher_groups)}'

    def cloned(
        self,
        *,
        group: Group | str | Missing = MISSING,
        include_higher_groups: bool | Missing = MISSING,
        inverted: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'group': group,
                'include_higher_groups': include_higher_groups,
                'inverted': inverted,
            },
        )
