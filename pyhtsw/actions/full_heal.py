from typing import final

from pyhtsw.expression.expression import Expression
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

__all__ = (
    'FullHealExpression',
    'full_heal',
)


@final
class FullHealExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='HEAL',
        limit=5,
        effects=Effects.of(
            writes=(
                Resource.HEALTH,
                Resource.HUNGER,
            ),
        ),
        display_name='Full Heal',
        forbidden_events=('Player Quit',),
    )

    def into_htsl(self) -> str:
        return 'fullHeal'


def full_heal() -> None:
    FullHealExpression().write()
