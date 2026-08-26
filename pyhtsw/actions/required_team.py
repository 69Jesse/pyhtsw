from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with

from ..expression.condition.condition import Condition
from .team import Team

__all__ = ('RequiredTeam',)


@final
class RequiredTeam(Condition):
    team: Team | None

    def __init__(
        self,
        team: Team | str | None,
    ) -> None:
        self.team = team if not isinstance(team, str) else Team(team)

    def into_htsl_raw(self) -> str:
        name = self.team.name if self.team is not None else 'None'
        return f'hasTeam {self.inline_quoted(name)}'

    def cloned(
        self,
        *,
        team: Team | str | None | Missing = MISSING,
        inverted: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'team': team,
                'inverted': inverted,
            },
        )
