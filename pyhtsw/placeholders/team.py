import re
from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.compiler.registry import ActionMeta
from pyhtsw.compiler.schedule import Effects, Resource
from pyhtsw.declarations.team import Team
from pyhtsw.execute.backend_type import BackendType, JavaLong
from pyhtsw.expression.housing_type import HousingType
from pyhtsw.internal_type import InternalType
from pyhtsw.placeholders.base import PlaceholderCheckable

__all__ = (
    'TeamColorPlaceholder',
    'TeamColor',
    'TeamNamePlaceholder',
    'TeamName',
    'TeamPlayersPlaceholder',
    'TeamPlayers',
    'TeamTagPlaceholder',
    'TeamTag',
)


@final
class TeamColorPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.team.color%')),
    pattern_factory=lambda _: TeamColor,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.TEAM,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.team.color%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''


TeamColor = TeamColorPlaceholder()


@final
class TeamNamePlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.team.name%')),
    pattern_factory=lambda _: TeamName,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.TEAM,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.team.name%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''


TeamName = TeamNamePlaceholder()


def _team_players_factory(match: re.Match[str]) -> 'TeamPlayersPlaceholder':
    team = match.group(1)
    return TeamPlayersPlaceholder(team if team else None)


@final
class TeamPlayersPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(r'%player\.team\.players(?:/([^%]*))?%'),
    pattern_factory=_team_players_factory,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.TEAM,)),
    )

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


@final
class TeamTagPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.team.tag%')),
    pattern_factory=lambda _: TeamTag,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.TEAM,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.team.tag%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''


TeamTag = TeamTagPlaceholder()
