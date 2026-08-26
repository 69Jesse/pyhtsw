import re
from typing import final

from pyhtsw.execute.backend_type import BackendType
from pyhtsw.internal_type import InternalType
from pyhtsw.placeholders import PlaceholderCheckable
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects

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
    htsw_meta = ActionMeta(
        effects=Effects.of(),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%house.visitingrules%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''


HouseVisitingRules = HouseVisitingRulesPlaceholder()
