import re
import time
from typing import final

from ..execute.backend_type import BackendType, JavaLong
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = (
    'DateUnixMSPlaceholder',
    'DateUnixMS',
    'DateUnixPlaceholder',
    'DateUnix',
)


@final
class DateUnixPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%date.unix%')),
    pattern_factory=lambda _: DateUnix,
):
    def __init__(self) -> None:
        super().__init__(
            placeholder='%date.unix%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(int(time.time()))


DateUnix = DateUnixPlaceholder()


@final
class DateUnixMSPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%date.unix.ms%')),
    pattern_factory=lambda _: DateUnixMS,
):
    def __init__(self) -> None:
        super().__init__(
            placeholder='%date.unix.ms%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(int(time.time() * 1000))


DateUnixMS = DateUnixMSPlaceholder()
