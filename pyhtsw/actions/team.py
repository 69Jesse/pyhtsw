from typing import TYPE_CHECKING

from ..placeholders import PlaceholderCheckable

if TYPE_CHECKING:
    from ..importable import TeamImportable
    from ..stats.team_stat import TeamStat


__all__ = ('Team',)


class Team:
    name: str
    # Set by create_team; None for a plain reference to a team declared
    # elsewhere (or in-game).
    __htsw_importable__: 'TeamImportable | None' = None

    def __init__(self, name: str) -> None:
        self.name = name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Team):
            return NotImplemented
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def stat(self, key: str) -> 'TeamStat':
        from ..stats.team_stat import TeamStat

        return TeamStat(key, self)

    def players(self) -> PlaceholderCheckable:
        from .team_players import TeamPlayers

        return TeamPlayers(self)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.name}>'
