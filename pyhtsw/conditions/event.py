from typing import TYPE_CHECKING, Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.compiler.registry import ConditionMeta
from pyhtsw.declarations.item import (
    Item,
    item_action_reference,
    item_referenced_importables,
)
from pyhtsw.expression.condition.comparison_condition import ComparisonOperator
from pyhtsw.expression.condition.condition import Condition
from pyhtsw.expression.housing_type import HousingType, housing_type_as_rhs
from pyhtsw.generated.enums import (
    DamageCauseName,
    FishingEnvironmentName,
    PortalTypeName,
)

__all__ = (
    'DamageAmountCondition',
    'DamageAmount',
    'DamageCause',
    'FishingEnvironment',
    'PortalType',
    'BlockType',
)

if TYPE_CHECKING:
    from pyhtsw.checkable import Checkable


@final
class DamageAmountCondition(Condition):
    """`damageAmount > 5`. Housing exposes the damage amount only to this
    condition — there is no `%damage.amount%` placeholder — so it is not a
    Checkable and cannot be used as a value."""

    htsw_meta = ConditionMeta(
        htsw_name='COMPARE_DAMAGE',
        limit=20,
        reads=frozenset(()),
        display_name='Damage Amount',
        scoped_events=('player_damage',),
    )

    operator: ComparisonOperator
    amount: 'Checkable | HousingType'

    def __init__(
        self,
        operator: ComparisonOperator,
        amount: 'Checkable | HousingType',
    ) -> None:
        self.operator = operator
        self.amount = amount

    def into_htsl_raw(self) -> str:
        from pyhtsw.checkable import Checkable

        if isinstance(self.amount, Checkable):
            rhs = self.amount.into_string_rhs()
        else:
            rhs = housing_type_as_rhs(self.amount)
        return f'damageAmount {self.operator.value} {rhs}'

    def cloned(
        self,
        *,
        operator: ComparisonOperator | Missing = MISSING,
        amount: 'Checkable | HousingType | Missing' = MISSING,
        inverted: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'operator': operator,
                'amount': amount,
                'inverted': inverted,
            },
        )


@final
class _DamageAmount:
    def _compare(
        self,
        operator: ComparisonOperator,
        other: 'Checkable | HousingType',
    ) -> DamageAmountCondition:
        return DamageAmountCondition(operator, other)

    def __eq__(self, other: 'Checkable | HousingType') -> DamageAmountCondition:  # type: ignore[override]
        return self._compare(ComparisonOperator.Equal, other)

    def __gt__(self, other: 'Checkable | HousingType') -> DamageAmountCondition:
        return self._compare(ComparisonOperator.GreaterThan, other)

    def __lt__(self, other: 'Checkable | HousingType') -> DamageAmountCondition:
        return self._compare(ComparisonOperator.LessThan, other)

    def __ge__(self, other: 'Checkable | HousingType') -> DamageAmountCondition:
        return self._compare(ComparisonOperator.GreaterThanOrEqual, other)

    def __le__(self, other: 'Checkable | HousingType') -> DamageAmountCondition:
        return self._compare(ComparisonOperator.LessThanOrEqual, other)

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:
        return 'DamageAmount'


DamageAmount = _DamageAmount()


@final
class DamageCause(Condition):
    htsw_meta = ConditionMeta(
        htsw_name='DAMAGE_CAUSE',
        limit=20,
        reads=frozenset(()),
        display_name='Damage Cause',
        scoped_events=('player_damage',),
    )

    damage_cause: str

    def __init__(
        self,
        damage_cause: DamageCauseName,
    ) -> None:
        self.damage_cause = damage_cause

    def into_htsl_raw(self) -> str:
        return f'damageCause {self.inline_quoted(self.damage_cause)}'

    def cloned(
        self,
        *,
        damage_cause: DamageCauseName | Missing = MISSING,
        inverted: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'damage_cause': damage_cause,
                'inverted': inverted,
            },
        )


@final
class FishingEnvironment(Condition):
    htsw_meta = ConditionMeta(
        htsw_name='FISHING_ENVIRONMENT',
        limit=20,
        reads=frozenset(()),
        display_name='Fishing Environment',
        scoped_events=('fish_caught',),
    )

    environment: FishingEnvironmentName

    def __init__(
        self,
        environment: FishingEnvironmentName,
    ) -> None:
        self.environment = environment

    def into_htsl_raw(self) -> str:
        return f'fishingEnv {self.inline_quoted(self.environment)}'

    def cloned(
        self,
        *,
        environment: FishingEnvironmentName | Missing = MISSING,
        inverted: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'environment': environment,
                'inverted': inverted,
            },
        )


@final
class PortalType(Condition):
    htsw_meta = ConditionMeta(
        htsw_name='PORTAL_TYPE',
        limit=20,
        reads=frozenset(()),
        display_name='Portal Type',
        scoped_events=('player_enter_portal',),
    )

    portal: PortalTypeName

    def __init__(
        self,
        portal: PortalTypeName,
    ) -> None:
        self.portal = portal

    def into_htsl_raw(self) -> str:
        return f'portal {self.portal}'

    def cloned(
        self,
        *,
        portal: PortalTypeName | Missing = MISSING,
        inverted: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'portal': portal,
                'inverted': inverted,
            },
        )


@final
class BlockType(Condition):
    htsw_meta = ConditionMeta(
        htsw_name='BLOCK_TYPE',
        limit=20,
        reads=frozenset(()),
        display_name='Block Type',
        scoped_events=('player_block_break',),
    )

    block: Item
    match_type_only: bool

    def __init__(
        self,
        block: Item,
        match_type_only: bool = False,
    ) -> None:
        self.block = block
        self.match_type_only = match_type_only

    def into_htsl_raw(self) -> str:
        name = item_action_reference(self.block)
        return (
            f'blockType {self.inline_quoted(name)} {self.inline(self.match_type_only)}'
        )

    def referenced_importables(self) -> list[tuple[str, str]]:
        return item_referenced_importables(self.block)

    def cloned(
        self,
        *,
        block: Item | Missing = MISSING,
        match_type_only: bool | Missing = MISSING,
        inverted: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'block': block,
                'match_type_only': match_type_only,
                'inverted': inverted,
            },
        )
