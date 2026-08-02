from collections.abc import Callable

from ..block import NamedBlock
from ..container import get_current_container
from ..importable import CommandImportable
from ..types import ALL_COMMAND_MODES
from ..utils.caller import caller_module
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

        container = get_current_container()
        container.add_block(block)
        importable = CommandImportable(
            block,
            name=name,
            mode=mode,
            required_priority=required_priority,
            listed=listed,
        )
        importable.module = caller_module()
        container.register_importable(importable)
        command.__htsw_importable__ = importable
        return command

    return decorator
