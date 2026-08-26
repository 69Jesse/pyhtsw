import re
from typing import TYPE_CHECKING, Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.declarations.declared import declared_name
from pyhtsw.expression.housing_type import HousingType, housing_type_from_string
from pyhtsw.internal_type import InternalType
from pyhtsw.stats.player_stat import _split_parts
from pyhtsw.stats.stat import Stat

if TYPE_CHECKING:
    from pyhtsw.declarations.team import Team

__all__ = ('TeamStat',)


def _team_stat_factory(match: re.Match[str]) -> 'TeamStat':
    parts = _split_parts(match.group(1))
    name = parts[0] if len(parts) > 0 else ''
    team = parts[1] if len(parts) > 1 else None
    stat = TeamStat(name, team=team)
    if len(parts) > 2:
        stat = stat.with_fallback(housing_type_from_string(parts[2]))
    return stat


@final
class TeamStat(
    Stat,
    pattern=re.compile(r'%var\.team/([^%]+)%'),
    pattern_factory=_team_stat_factory,
):
    team: str | None

    def __init__(
        self,
        name: str,
        /,
        *,
        team: 'Team | str | None' = None,
        internal_type: InternalType = InternalType.ANY,
        fallback_value: HousingType | None = None,
        auto_unset: bool = True,
    ) -> None:
        super().__init__(
            name,
            internal_type=internal_type,
            fallback_value=fallback_value,
            auto_unset=auto_unset,
        )
        self.team = declared_name(team)

    def into_hashable(self) -> tuple[object, ...]:
        return (
            *super().into_hashable(),
            self.team,
        )

    @staticmethod
    def left_side_keyword() -> str:
        return 'teamvar'

    @staticmethod
    def right_side_keyword() -> str:
        return 'team'

    def into_string_lhs(self) -> str:
        value = super().into_string_lhs()
        if self.team is not None:
            return f'{value} "{self.team}"'
        return value

    def into_string_middle(self, include_fallback_value: bool = True) -> str:
        value = super().into_string_middle(
            include_fallback_value=include_fallback_value,
        )
        if self.team is not None or value:
            name = self.team if self.team is not None else 'None'
            if ' ' in name:
                name = f'"{name}"'
            return f' {name}{value}'
        return value

    def cloned(
        self,
        *,
        name: str | Missing = MISSING,
        team: 'Team | str | None | Missing' = MISSING,
        internal_type: InternalType | Missing = MISSING,
        fallback_value: HousingType | None | Missing = MISSING,
        auto_unset: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'name': name,
                'team': team,
                'internal_type': internal_type,
                'fallback_value': fallback_value,
                'auto_unset': auto_unset,
            },
        )

    def equals_raw(self, other: object) -> bool:
        if not super().equals_raw(other):
            return False
        if not isinstance(other, TeamStat):
            return False
        return self.team == other.team

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.name}, {repr(self.team)} {self.internal_type.name}>'
