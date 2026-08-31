from typing import TYPE_CHECKING

from pyhtsw.compiler.importable import TeamImportable
from pyhtsw.declarations.declared import Declared, declared_field, register_importable
from pyhtsw.generated.enums import HousingColor
from pyhtsw.placeholders.base import PlaceholderCheckable

__all__ = ('Team',)

if TYPE_CHECKING:
    from pyhtsw.stats.team_stat import TeamStat


class Team(Declared):
    __htsw_kind__ = 'teams'
    __htsw_factory__ = 'Team'

    tag: declared_field[str | None] = declared_field()
    color: 'declared_field[HousingColor | None]' = declared_field()
    friendly_fire: declared_field[bool | None] = declared_field()

    def __init__(
        self,
        name: str,
        *,
        tag: str | None = None,
        color: HousingColor | None = None,
        friendly_fire: bool | None = None,
    ) -> None:
        """Declare a team importable. A team that already exists in the house
        is referenced by its plain name instead."""
        super().__init__(name)
        self.__htsw_importable__ = register_importable(
            TeamImportable(
                name=name,
                tag=tag,
                color=color,
                friendly_fire=friendly_fire,
            ),
        )

    def stat(self, name: str) -> 'TeamStat':
        from pyhtsw.stats.team_stat import TeamStat

        return TeamStat(name, team=self)

    def players(self) -> PlaceholderCheckable:
        from pyhtsw.placeholders.team import TeamPlayers

        return TeamPlayers(self)
