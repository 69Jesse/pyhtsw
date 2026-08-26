from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with

from ..expression.condition.condition import Condition
from ..types import ALL_DAMAGE_CAUSES

__all__ = ('DamageCause',)


@final
class DamageCause(Condition):
    damage_cause: str

    def __init__(
        self,
        damage_cause: ALL_DAMAGE_CAUSES,
    ) -> None:
        self.damage_cause = damage_cause

    def into_htsl_raw(self) -> str:
        return f'damageCause {self.inline_quoted(self.damage_cause)}'

    def cloned(
        self,
        *,
        damage_cause: ALL_DAMAGE_CAUSES | Missing = MISSING,
        inverted: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'damage_cause': damage_cause,
                'inverted': inverted,
            },
        )
