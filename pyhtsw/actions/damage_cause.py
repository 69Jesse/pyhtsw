from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.expression.condition.condition import Condition
from pyhtsw.registry import ConditionMeta
from pyhtsw.types import ALL_DAMAGE_CAUSES

__all__ = ('DamageCause',)


@final
class DamageCause(Condition):
    htsw_meta = ConditionMeta(
        htsw_name='DAMAGE_CAUSE',
        limit=20,
        reads=frozenset(()),
        display_name='Damage Cause',
        scoped_events=('Player Damage',),
    )

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
