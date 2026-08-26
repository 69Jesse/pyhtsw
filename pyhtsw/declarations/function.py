from collections.abc import Callable
from typing import TYPE_CHECKING

from pyhtsw.compiler.importable import FunctionImportable
from pyhtsw.declarations.declared import Declared, declared_field, register_importable

__all__ = (
    'Function',
    'create_function',
)

if TYPE_CHECKING:
    from pyhtsw.compiler.block import FunctionBlock
    from pyhtsw.declarations.item import Item


class Function(Declared):
    __htsw_kind__ = 'functions'
    __htsw_factory__ = 'create_function'

    block: 'FunctionBlock | None'

    repeat_ticks: declared_field[int | None] = declared_field()
    icon: 'declared_field[Item | None]' = declared_field()

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.block = None


if TYPE_CHECKING:
    from pyhtsw.declarations.item import Item


def create_function(
    name: str,
    *,
    repeat_ticks: int | None = None,
    icon: 'Item | None' = None,
) -> Callable[[Callable[[], None]], Function]:
    def decorator(callback: Callable[[], None]) -> Function:
        from pyhtsw.compiler.block import FunctionBlock
        from pyhtsw.compiler.container import get_current_container

        function = Function(name=name)
        block = FunctionBlock(function=function, callback=callback)

        get_current_container().add_block(block)
        function.__htsw_importable__ = register_importable(
            FunctionImportable(
                block,
                name=name,
                repeat_ticks=repeat_ticks,
                icon=icon,
            ),
        )
        return function

    return decorator
