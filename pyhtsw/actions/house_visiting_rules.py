import re
from typing import final

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = (
    'HouseVisitingRulesPlaceholder',
    'HouseVisitingRules',
)


@final
class HouseVisitingRulesPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%house.visitingrules%')),
    pattern_factory=lambda _: HouseVisitingRules,
):
    def __init__(self) -> None:
        super().__init__(
            placeholder='%house.visitingrules%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''


HouseVisitingRules = HouseVisitingRulesPlaceholder()
