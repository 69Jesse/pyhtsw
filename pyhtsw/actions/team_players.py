import re
from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.expression.housing_type import HousingType

from ..execute.backend_type import BackendType, JavaLong
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable
from .team import Team

__all__ = (
    'TeamPlayersPlaceholder',
    'TeamPlayers',
)


def _team_players_factory(match: re.Match[str]) -> 'TeamPlayersPlaceholder':
    team = match.group(1)
    return TeamPlayersPlaceholder(team if team else None)


@final
class TeamPlayersPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(r'%player\.team\.players(?:/([^%]*))?%'),
    pattern_factory=_team_players_factory,
):
    team: Team | None

    def __init__(self, team: Team | str | None = None) -> None:
        if team is None:
            key = '%player.team.players%'
        else:
            team = team if isinstance(team, Team) else Team(team)
            key = f'%player.team.players/{team.name}%'
        self.team = team
        super().__init__(
            placeholder=key,
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(0)

    def cloned(
        self,
        *,
        team: Team | str | None | Missing = MISSING,
        internal_type: InternalType | Missing = MISSING,
        fallback_value: HousingType | None | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'team': team,
                'internal_type': internal_type,
                'fallback_value': fallback_value,
            },
        )


def TeamPlayers(
    team: Team | str | None,
) -> TeamPlayersPlaceholder:
    return TeamPlayersPlaceholder(team)
