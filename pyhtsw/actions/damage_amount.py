from typing import TYPE_CHECKING, final

from ..expression.condition.comparison_condition import ComparisonOperator
from ..expression.condition.condition import Condition
from ..expression.housing_type import HousingType, housing_type_as_rhs

if TYPE_CHECKING:
    from ..checkable import Checkable


__all__ = (
    'DamageAmountCondition',
    'DamageAmount',
)


@final
class DamageAmountCondition(Condition):
    """`damageAmount > 5`. Housing exposes the damage amount only to this
    condition — there is no `%damage.amount%` placeholder — so it is not a
    Checkable and cannot be used as a value."""

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
        from ..checkable import Checkable

        if isinstance(self.amount, Checkable):
            rhs = self.amount.into_string_rhs()
        else:
            rhs = housing_type_as_rhs(self.amount)
        return f'damageAmount {self.operator.value} {rhs}'

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, DamageAmountCondition):
            return False
        return self.operator is other.operator and self.equals_or_eq(
            self.amount,
            other.amount,
        )

    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}<{self.operator.value} {self.amount} '
            f'inverted={self.inverted}>'
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
