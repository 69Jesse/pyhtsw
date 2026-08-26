import re
from typing import final

from pyhtsw.execute.backend_type import BackendType, JavaLong
from pyhtsw.internal_type import InternalType
from pyhtsw.placeholders import PlaceholderCheckable
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects

__all__ = (
    'HouseGuestsPlaceholder',
    'HouseGuests',
)


@final
class HouseGuestsPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%house.guests%')),
    pattern_factory=lambda _: HouseGuests,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%house.guests%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(0)


HouseGuests = HouseGuestsPlaceholder()
