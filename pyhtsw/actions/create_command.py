from collections.abc import Callable

from ..block import NamedBlock
from ..container import get_current_container
from ..declared import register_importable
from ..importable import CommandImportable
from ..types import ALL_COMMAND_MODES
from .command import Command

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
