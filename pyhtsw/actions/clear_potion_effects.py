from typing import final

from ..expression.expression import Expression

__all__ = (
    'ClearPotionEffectsExpression',
    'clear_potion_effects',
)


@final
class ClearPotionEffectsExpression(Expression):
    def into_htsl(self) -> str:
        return 'clearEffects'


def clear_potion_effects() -> None:
    ClearPotionEffectsExpression().write()
