from typing import TYPE_CHECKING, cast

from ..declared import Declared

if TYPE_CHECKING:
    from ..importable import EventName


__all__ = ('Event',)


class Event(Declared):
    """A Housing event handler. Like a Command it is not callable from HTSL -
    the event fires it - so this only carries the event name for reference."""

    __htsw_kind__ = 'events'
    __htsw_factory__ = 'create_event'

    @property
    def event(self) -> 'EventName':
        return cast('EventName', self.name)
