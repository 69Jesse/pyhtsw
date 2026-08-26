from typing import TYPE_CHECKING

from pyhtsw.declared import Declared, declared_field
from pyhtsw.placeholders import PlaceholderCheckable

if TYPE_CHECKING:
    from pyhtsw.stats.team_stat import TeamStat
    from pyhtsw.types import ALL_HOUSING_COLORS


__all__ = ('Team',)


class Team(Declared):
    __htsw_kind__ = 'teams'
    __htsw_factory__ = 'create_team'

    tag: declared_field[str | None] = declared_field()
    color: 'declared_field[ALL_HOUSING_COLORS | None]' = declared_field()
    friendly_fire: declared_field[bool | None] = declared_field()

    def stat(self, key: str) -> 'TeamStat':
        from pyhtsw.stats.team_stat import TeamStat

        return TeamStat(key, self)

    def players(self) -> PlaceholderCheckable:
        from pyhtsw.actions.team_players import TeamPlayers

        return TeamPlayers(self)
