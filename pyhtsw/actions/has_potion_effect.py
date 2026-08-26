from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.expression.condition.condition import Condition
from pyhtsw.registry import ConditionMeta
from pyhtsw.schedule import Resource
from pyhtsw.types import ALL_POTION_EFFECTS

__all__ = ('HasPotionEffect',)


@final
class HasPotionEffect(Condition):
    htsw_meta = ConditionMeta(
        htsw_name='REQUIRE_POTION_EFFECT',
        limit=22,
        reads=frozenset((Resource.POTIONS,)),
    )

    effect: ALL_POTION_EFFECTS

    def __init__(
        self,
        effect: ALL_POTION_EFFECTS,
    ) -> None:
        self.effect = effect

    def into_htsl_raw(self) -> str:
        return f'hasPotion {self.inline_quoted(self.effect)}'

    def cloned(
        self,
        *,
        effect: ALL_POTION_EFFECTS | Missing = MISSING,
        inverted: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'effect': effect,
                'inverted': inverted,
            },
        )
