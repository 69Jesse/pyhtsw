from typing import Self, final

from pyhtsw.actions.team import Team
from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.expression.expression import Expression
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

__all__ = (
    'SetPlayerTeamExpression',
    'set_player_team',
)


@final
class SetPlayerTeamExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='SET_TEAM',
        limit=1,
        effects=Effects.of(writes=(Resource.TEAM,)),
        display_name='Set Player Team',
        forbidden_events=('Player Quit',),
    )

    team: Team

    def __init__(self, team: Team) -> None:
        self.team = team

    def into_htsl(self) -> str:
        return f'setTeam {self.inline_quoted(self.team.name)}'

    def cloned(
        self,
        *,
        team: Team | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'team': team,
            },
        )


def set_player_team(team: Team | str) -> None:
    team = team if isinstance(team, Team) else Team(team)
    SetPlayerTeamExpression(team=team).write()
