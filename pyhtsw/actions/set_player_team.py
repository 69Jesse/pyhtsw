from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with

from ..expression.expression import Expression
from .team import Team

__all__ = (
    'SetPlayerTeamExpression',
    'set_player_team',
)


@final
class SetPlayerTeamExpression(Expression):
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

    def equals(self, other: object) -> bool:
        if not isinstance(other, SetPlayerTeamExpression):
            return False
        return self.team.name == other.team.name

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.team.name}>'


def set_player_team(team: Team | str) -> None:
    team = team if isinstance(team, Team) else Team(team)
    SetPlayerTeamExpression(team=team).write()
