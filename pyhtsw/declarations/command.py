from collections.abc import Callable
from typing import TYPE_CHECKING

from pyhtsw.compiler.block import NamedBlock
from pyhtsw.compiler.container import get_current_container
from pyhtsw.compiler.importable import CommandImportable
from pyhtsw.declarations.declared import Declared, declared_field, register_importable
from pyhtsw.types import ALL_COMMAND_MODES

__all__ = (
    'Command',
    'command',
)

if TYPE_CHECKING:
    from pyhtsw.types import ALL_COMMAND_MODES


class Command(Declared):
    """A custom `/command` importable. Unlike a Function it is not callable
    from HTSL - Housing has no trigger-command action - so this only carries
    the name for reference and reexport."""

    __htsw_kind__ = 'commands'
    __htsw_factory__ = '@command'

    mode: 'declared_field[ALL_COMMAND_MODES | None]' = declared_field()
    required_priority: declared_field[int | None] = declared_field()
    listed: declared_field[bool | None] = declared_field()


def command(
    name: str,
    *,
    mode: ALL_COMMAND_MODES | None = None,
    required_priority: int | None = None,
    listed: bool | None = None,
) -> Callable[[Callable[[], None]], Command]:
    def decorator(callback: Callable[[], None]) -> Command:
        value = Command(name=name)
        block = NamedBlock(
            f'command {name}',
            callback=callback,
            importable_kind='commands',
        )

        get_current_container().add_block(block)
        value.__htsw_importable__ = register_importable(
            CommandImportable(
                block,
                name=name,
                mode=mode,
                required_priority=required_priority,
                listed=listed,
            ),
        )
        return value

    return decorator
