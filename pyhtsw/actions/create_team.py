from ..declared import register_importable
from ..importable import TeamImportable
from ..types import ALL_HOUSING_COLORS
from .team import Team

__all__ = ('create_team',)


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
