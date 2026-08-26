import random
import re
from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.execute.backend_type import BackendType, JavaLong
from pyhtsw.expression.housing_type import HousingType
from pyhtsw.internal_type import InternalType
from pyhtsw.placeholders import PlaceholderCheckable
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

__all__ = (
    'RandomWholePlaceholder',
    'RandomWhole',
)


def _random_whole_factory(match: re.Match[str]) -> 'RandomWholePlaceholder':
    return RandomWholePlaceholder(int(match.group(1)), int(match.group(2)))


@final
class RandomWholePlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(r'%random\.whole/(-?\d+) (-?\d+)%'),
    pattern_factory=_random_whole_factory,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.VOLATILE,), writes=(Resource.VOLATILE,)),
    )

    lower_bound: int
    exclusive_upper_bound: int

    def __init__(self, lower_bound: int, exclusive_upper_bound: int) -> None:
        self.lower_bound = lower_bound
        self.exclusive_upper_bound = exclusive_upper_bound
        if self.exclusive_upper_bound <= self.lower_bound:
            raise ValueError('exclusive_upper_bound must be greater than lower_bound')
        key = f'%random.whole/{lower_bound} {exclusive_upper_bound}%'
        super().__init__(
            placeholder=key,
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(
            random.randint(self.lower_bound, self.exclusive_upper_bound - 1),
        )

    def cloned(
        self,
        *,
        lower_bound: int | Missing = MISSING,
        exclusive_upper_bound: int | Missing = MISSING,
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


def RandomWhole(
    lower_bound: int,
    exclusive_upper_bound: int,
) -> RandomWholePlaceholder:
    return RandomWholePlaceholder(lower_bound, exclusive_upper_bound)
