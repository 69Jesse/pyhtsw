from typing import TYPE_CHECKING

from pyhtsw.declared import Declared, declared_field

if TYPE_CHECKING:
    from pyhtsw.types import ALL_COMMAND_MODES


__all__ = ('Command',)


class Command(Declared):
    """A custom `/command` importable. Unlike a Function it is not callable
    from HTSL - Housing has no trigger-command action - so this only carries
    the name for reference and reexport."""

    __htsw_kind__ = 'commands'
    __htsw_factory__ = 'create_command'

    mode: 'declared_field[ALL_COMMAND_MODES | None]' = declared_field()
    required_priority: declared_field[int | None] = declared_field()
    listed: declared_field[bool | None] = declared_field()
