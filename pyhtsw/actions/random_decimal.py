import random
import re
from typing import Self, final

import numpy as np

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.expression.housing_type import HousingType
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = (
    'RandomDecimalPlaceholder',
    'RandomDecimal',
)


def _random_decimal_factory(match: re.Match[str]) -> 'RandomDecimalPlaceholder':
    return RandomDecimalPlaceholder(float(match.group(1)), float(match.group(2)))


@final
class RandomDecimalPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(r'%random\.decimal/([\d.\-]+) ([\d.\-]+)%'),
    pattern_factory=_random_decimal_factory,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.VOLATILE,), writes=(Resource.VOLATILE,)),
    )

    lower_bound: float
    exclusive_upper_bound: float

    def __init__(self, lower_bound: float, exclusive_upper_bound: float) -> None:
        self.lower_bound = lower_bound
        self.exclusive_upper_bound = exclusive_upper_bound
        key = f'%random.decimal/{lower_bound} {exclusive_upper_bound}%'
        if self.exclusive_upper_bound <= self.lower_bound:
            raise ValueError('exclusive_upper_bound must be greater than lower_bound')
        super().__init__(
            placeholder=key,
            constant_internal_type=InternalType.DOUBLE,
        )

    def get_backend_value(self) -> BackendType:
        return np.float64(random.uniform(self.lower_bound, self.exclusive_upper_bound))

    def cloned(
        self,
        *,
        lower_bound: float | Missing = MISSING,
        exclusive_upper_bound: float | Missing = MISSING,
        internal_type: InternalType | Missing = MISSING,
        fallback_value: HousingType | None | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'lower_bound': lower_bound,
                'exclusive_upper_bound': exclusive_upper_bound,
                'internal_type': internal_type,
                'fallback_value': fallback_value,
            },
        )


def RandomDecimal(
    lower_bound: float,
    exclusive_upper_bound: float,
) -> RandomDecimalPlaceholder:
    return RandomDecimalPlaceholder(lower_bound, exclusive_upper_bound)
