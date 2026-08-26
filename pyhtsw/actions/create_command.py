from collections.abc import Callable

from pyhtsw.actions.command import Command
from pyhtsw.block import NamedBlock
from pyhtsw.container import get_current_container
from pyhtsw.declared import register_importable
from pyhtsw.importable import CommandImportable
from pyhtsw.types import ALL_COMMAND_MODES

__all__ = ('create_command',)


def create_command(
    name: str,
    *,
    mode: ALL_COMMAND_MODES | None = None,
    required_priority: int | None = None,
    listed: bool | None = None,
) -> Callable[[Callable[[], None]], Command]:
    def decorator(callback: Callable[[], None]) -> Command:
        command = Command(name=name)
        block = NamedBlock(
            f'command {name}',
            callback=callback,
            importable_kind='commands',
        )

        get_current_container().add_block(block)
        command.__htsw_importable__ = register_importable(
            CommandImportable(
                block,
                name=name,
                mode=mode,
                required_priority=required_priority,
                listed=listed,
            ),
        )
        return command

    return decorator
