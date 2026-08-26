from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with

from ..expression.expression import Expression
from .group import Group

__all__ = (
    'ChangePlayerGroupExpression',
    'change_player_group',
)


@final
class ChangePlayerGroupExpression(Expression):
    group: Group
    demotion_protection: bool

    def __init__(self, group: Group, demotion_protection: bool = True) -> None:
        self.group = group
        self.demotion_protection = demotion_protection

    def into_htsl(self) -> str:
        return f'changePlayerGroup {self.inline_quoted(self.group.name)} {self.inline(self.demotion_protection)}'

    def cloned(
        self,
        *,
        group: Group | Missing = MISSING,
        demotion_protection: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'group': group,
                'demotion_protection': demotion_protection,
            },
        )


def change_player_group(group: Group | str, demotion_protection: bool = True) -> None:
    group = group if isinstance(group, Group) else Group(group)
    ChangePlayerGroupExpression(
        group=group,
        demotion_protection=demotion_protection,
    ).write()
