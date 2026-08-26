from collections.abc import Callable
from typing import Any, Literal

from pyhtsw.compiler.block import NamedBlock
from pyhtsw.compiler.container import get_current_container
from pyhtsw.compiler.importable import (
    Bounds,
    Coord,
    Handler,
    RegionImportable,
    call_with_args,
)
from pyhtsw.declarations.declared import Declared, declared_field, register_importable

__all__ = ('Region',)

Side = Literal['enter', 'exit']


class Region(Declared):
    __htsw_kind__ = 'regions'
    __htsw_factory__ = 'Region'

    bounds: declared_field[Bounds | None] = declared_field()

    def __init__(
        self,
        name: str,
        bounds: Bounds | None = None,
        *,
        on_enter: Handler | None = None,
        on_exit: Handler | None = None,
    ) -> None:
        super().__init__(name)
        self.__htsw_importable__ = register_importable(
            RegionImportable(name=name, bounds=bounds),
        )
        if on_enter is not None:
            self.attach('enter', on_enter)
        if on_exit is not None:
            self.attach('exit', on_exit)

    @property
    def declared(self) -> RegionImportable:
        importable = self.declaration()
        assert isinstance(importable, RegionImportable)
        return importable

    def corners(self, first: Coord, second: Coord) -> None:
        """Set `bounds` from two opposite corners in either order, the way the
        in-game region tool hands them to you."""
        (ax, ay, az), (bx, by, bz) = first, second
        self.bounds = (
            (min(ax, bx), min(ay, by), min(az, bz)),
            (max(ax, bx), max(ay, by), max(az, bz)),
        )

    def attach(self, side: Side, handler: Handler) -> None:
        """Give this region an enter or exit handler after the fact."""
        importable = self.declared
        block = NamedBlock(
            f'{self.name} {side}',
            callback=lambda: call_with_args(handler, self),
            importable_kind='regions',
        )
        get_current_container().add_block(block)
        if side == 'enter':
            importable.on_enter = block
        else:
            importable.on_exit = block

    def on_enter(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """`@region.on_enter` - run these actions when a player walks in."""
        self.attach('enter', func)
        return func

    def on_exit(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """`@region.on_exit` - run these actions when a player walks out."""
        self.attach('exit', func)
        return func
