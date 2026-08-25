import re
from typing import final

from ..execute.backend_type import BackendType, JavaLong
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

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
    def __init__(self) -> None:
        super().__init__(
            placeholder='%house.cookies%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(0)


HouseCookies = HouseCookiesPlaceholder()
