from collections.abc import Callable

from pyhtsw.actions.event import Event
from pyhtsw.block import NamedBlock
from pyhtsw.container import get_current_container
from pyhtsw.declared import register_importable
from pyhtsw.importable import EventImportable, EventName

__all__ = ('create_event',)


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
