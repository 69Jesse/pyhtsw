from collections.abc import Callable
from typing import TYPE_CHECKING, cast

from pyhtsw.compiler.block import NamedBlock
from pyhtsw.compiler.container import get_current_container
from pyhtsw.compiler.importable import EventImportable, EventName
from pyhtsw.declarations.declared import Declared, register_importable

__all__ = (
    'Event',
    'create_event',
)

if TYPE_CHECKING:
    from pyhtsw.compiler.importable import EventName


class Event(Declared):
    """A Housing event handler. Like a Command it is not callable from HTSL -
    the event fires it - so this only carries the event name for reference."""

    __htsw_kind__ = 'events'
    __htsw_factory__ = 'create_event'

    @property
    def event(self) -> 'EventName':
        return cast('EventName', self.name)


def create_event(event: EventName) -> Callable[[Callable[[], None]], Event]:
    def decorator(callback: Callable[[], None]) -> Event:
        block = NamedBlock(
            f'event {event}',
            callback=callback,
            importable_kind='events',
        )
        get_current_container().add_block(block)
        importable = register_importable(EventImportable(block, event=event))

        value = Event(event)
        value.__htsw_importable__ = importable
        return value

    return decorator
