import re
from typing import final

from pyhtsw.execute.backend_type import BackendType, JavaLong
from pyhtsw.internal_type import InternalType
from pyhtsw.placeholders import PlaceholderCheckable
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects

__all__ = (
    'HouseCookiesPlaceholder',
    'HouseCookies',
)


@final
class HouseCookiesPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%house.cookies%')),
    pattern_factory=lambda _: HouseCookies,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%house.cookies%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(0)


HouseCookies = HouseCookiesPlaceholder()
