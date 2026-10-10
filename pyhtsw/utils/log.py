import re
import sys
from typing import TYPE_CHECKING, Any

__all__ = ('log',)

ANSI_ESCAPE: re.Pattern[str] = re.compile(r'\x1b\[[0-9;]*m')


def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub('', text)


def _log(*args: object, **kwargs: Any) -> None:
    if not sys.stdout.isatty():
        args = tuple(strip_ansi(str(a)) for a in args)
    print(*args, **kwargs)


if TYPE_CHECKING:
    log = print
else:
    log = _log
