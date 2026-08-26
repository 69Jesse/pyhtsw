from typing import TYPE_CHECKING

from ..declared import Declared, declared_field

if TYPE_CHECKING:
    from ..block import FunctionBlock
    from .item import Item


__all__ = ('Function',)


class Function(Declared):
    __htsw_kind__ = 'functions'
    __htsw_factory__ = 'create_function'

    block: 'FunctionBlock | None'

    repeat_ticks: declared_field[int | None] = declared_field()
    icon: 'declared_field[Item | None]' = declared_field()

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.block = None
