from typing import TYPE_CHECKING

from pyhtsw.compiler.importable import TeamImportable
from pyhtsw.declarations.declared import Declared, declared_field, register_importable
from pyhtsw.placeholders.base import PlaceholderCheckable
from pyhtsw.types import ALL_HOUSING_COLORS

__all__ = (
    'Team',
    'create_team',
)

if TYPE_CHECKING:
    from pyhtsw.stats.team_stat import TeamStat
    from pyhtsw.types import ALL_HOUSING_COLORS


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
        from pyhtsw.placeholders.team import TeamPlayers

        return TeamPlayers(self)


def create_team(
    name: str,
    *,
    tag: str | None = None,
    color: ALL_HOUSING_COLORS | None = None,
    friendly_fire: bool | None = None,
) -> Team:
    """Declare a team importable and return the `Team` that actions and
    `TeamStat` already take, so a declared team is used exactly like an
    undeclared `Team(name)`."""
    team = Team(name)
    team.__htsw_importable__ = register_importable(
        TeamImportable(
            name=name,
            tag=tag,
            color=color,
            friendly_fire=friendly_fire,
        ),
    )
    return team
