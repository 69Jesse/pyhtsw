from typing import final

from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

from ..expression.expression import Expression

__all__ = (
    'KillPlayerExpression',
    'kill_player',
)


@final
class KillPlayerExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='KILL',
        limit=1,
        effects=Effects.of(
            writes=(
                Resource.EXPERIENCE,
                Resource.HEALTH,
                Resource.HUNGER,
                Resource.INVENTORY,
                Resource.POSITION,
                Resource.POTIONS,
            ),
        ),
        display_name='Kill Player',
        forbidden_in_events=True,
    )

    def into_htsl(self) -> str:
        return 'kill'


def kill_player() -> None:
    KillPlayerExpression().write()
