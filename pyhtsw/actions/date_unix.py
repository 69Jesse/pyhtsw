import re
import time
from typing import final

from pyhtsw.execute.backend_type import BackendType, JavaLong
from pyhtsw.internal_type import InternalType
from pyhtsw.placeholders import PlaceholderCheckable
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

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
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.VOLATILE,), writes=(Resource.VOLATILE,)),
    )

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
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.VOLATILE,), writes=(Resource.VOLATILE,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%date.unix.ms%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(int(time.time() * 1000))


DateUnixMS = DateUnixMSPlaceholder()
