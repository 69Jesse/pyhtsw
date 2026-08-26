from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with

from ..expression.expression import Expression
from ..types import ALL_POTION_EFFECTS

__all__ = (
    'ApplyPotionEffectExpression',
    'apply_potion_effect',
)


@final
class ApplyPotionEffectExpression(Expression):
    potion: ALL_POTION_EFFECTS
    duration: int
    level: int
    override_existing_effects: bool
    show_potion_icon: bool

    def __init__(
        self,
        potion: ALL_POTION_EFFECTS,
        duration: int = 60,
        level: int = 1,
        override_existing_effects: bool = False,
        show_potion_icon: bool = False,
    ) -> None:
        self.potion = potion
        self.duration = duration
        self.level = level
        self.override_existing_effects = override_existing_effects
        self.show_potion_icon = show_potion_icon

    def into_htsl(self) -> str:
        return (
            f'applyPotion {self.inline_quoted(self.potion)} {self.inline(self.duration)} {self.inline(self.level)}'
            f' {self.inline(self.override_existing_effects)} {self.inline(self.show_potion_icon)}'
        )

    def cloned(
        self,
        *,
        potion: ALL_POTION_EFFECTS | Missing = MISSING,
        duration: int | Missing = MISSING,
        level: int | Missing = MISSING,
        override_existing_effects: bool | Missing = MISSING,
        show_potion_icon: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'potion': potion,
                'duration': duration,
                'level': level,
                'override_existing_effects': override_existing_effects,
                'show_potion_icon': show_potion_icon,
            },
        )


def apply_potion_effect(
    potion: ALL_POTION_EFFECTS,
    duration: int = 60,
    level: int = 1,
    override_existing_effects: bool = False,
    show_potion_icon: bool = False,
) -> None:
    ApplyPotionEffectExpression(
        potion=potion,
        duration=duration,
        level=level,
        override_existing_effects=override_existing_effects,
        show_potion_icon=show_potion_icon,
    ).write()
