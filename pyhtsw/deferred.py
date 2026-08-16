import re
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from .checkable import Checkable

__all__ = (
    'register_deferred',
    'lookup_deferred',
    'find_deferred_ids',
    'text_has_deferred',
    'substitute_deferred',
)


_PREFIX = '\x00\x00<pyhtsw-deferred:'
_SUFFIX = '>\x00\x00'
_PATTERN = re.compile(re.escape(_PREFIX) + r'(\d+)' + re.escape(_SUFFIX))


class DeferredEntry(NamedTuple):
    checkable: 'Checkable'
    include_fallback_value: bool


_registry: dict[int, DeferredEntry] = {}
_counter = 0


def register_deferred(checkable: 'Checkable', include_fallback_value: bool) -> str:
    from .actions.no_fallback_values import no_fallback_values

    global _counter
    _counter += 1
    # Resolution happens long after the `NoFallbackValues` block has exited, so
    # capture it here instead.
    _registry[_counter] = DeferredEntry(
        checkable,
        include_fallback_value and not no_fallback_values(),
    )
    return f'{_PREFIX}{_counter}{_SUFFIX}'


def lookup_deferred(deferred_id: int) -> DeferredEntry:
    return _registry[deferred_id]


def text_has_deferred(text: str) -> bool:
    return _PATTERN.search(text) is not None


def find_deferred_ids(text: str) -> list[int]:
    found: dict[int, None] = {}
    for match in _PATTERN.finditer(text):
        found.setdefault(int(match.group(1)), None)
    return list(found)


def substitute_deferred(text: str, mapping: dict[int, str]) -> str:
    return _PATTERN.sub(
        lambda match: mapping.get(int(match.group(1)), match.group(0)),
        text,
    )
