from typing import final

from pyhtsw.expression.expression import Expression
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

__all__ = (
    'ClearPotionEffectsExpression',
    'clear_potion_effects',
)


@final
class ClearPotionEffectsExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='CLEAR_POTION_EFFECTS',
        limit=5,
        effects=Effects.of(writes=(Resource.POTIONS,)),
        display_name='Clear All Potion Effects',
        forbidden_events=('Player Quit',),
    )

    def into_htsl(self) -> str:
        return 'clearEffects'


def clear_potion_effects() -> None:
    ClearPotionEffectsExpression().write()
