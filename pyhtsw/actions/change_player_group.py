from typing import Self, final

from pyhtsw.actions.group import Group
from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.expression.expression import Expression
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

__all__ = (
    'ChangePlayerGroupExpression',
    'change_player_group',
)


@final
class ChangePlayerGroupExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='SET_GROUP',
        limit=1,
        effects=Effects.of(writes=(Resource.GROUP,)),
        display_name="Change Player's Group",
        forbidden_events=(
            'Group Change',
            'Player Quit',
        ),
    )

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
