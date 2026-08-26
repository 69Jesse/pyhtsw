from collections.abc import Callable
from typing import Any, Literal, overload

from pyhtsw.compiler.block import NamedBlock
from pyhtsw.compiler.container import get_current_container
from pyhtsw.compiler.importable import (
    Coord,
    Handler,
    NpcEquipment,
    NpcImportable,
    NpcSkin,
    call_with_args,
)
from pyhtsw.declarations.declared import Declared, declared_field, register_importable

__all__ = ('NPC', 'create_npc')

Which = Literal['left', 'right', 'both']


def _reject_click_conflict(name: str, **present: object) -> None:
    conflicting = [label for label, value in present.items() if value is not None]
    if conflicting:
        raise ValueError(
            f'NPC "{name}": on_click already means "right-click actions, and '
            f'left click redirects to them", so it cannot be combined with '
            f'{", ".join(sorted(conflicting))}.',
        )


class NPC(Declared):
    Equipment = NpcEquipment

    __htsw_kind__ = 'npcs'
    __htsw_factory__ = 'create_npc'

    pos: declared_field[Coord] = declared_field()
    skin: 'declared_field[NpcSkin | None]' = declared_field()
    equipment: 'declared_field[NpcEquipment | None]' = declared_field()
    look_at_players: declared_field[bool | None] = declared_field()
    hide_name_tag: declared_field[bool | None] = declared_field()
    left_click_redirect: declared_field[bool | None] = declared_field()

    __click_mode__: 'Which | None' = None

    def __init__(
        self,
        name: str,
        pos: Coord,
        *,
        on_click: Handler | None = None,
        on_left_click: Handler | None = None,
        on_right_click: Handler | None = None,
        left_click_redirect: bool | None = None,
        look_at_players: bool | None = None,
        hide_name_tag: bool | None = None,
        skin: NpcSkin | None = None,
        equipment: NpcEquipment | None = None,
    ) -> None:
        """Declare an NPC as a value. Prefer `create_npc(...)`, which is the
        same thing under a name matching `create_function` and friends."""
        super().__init__(name)
        self.__htsw_importable__ = register_importable(
            NpcImportable(
                name=name,
                pos=pos,
                left_click_redirect=left_click_redirect,
                look_at_players=look_at_players,
                hide_name_tag=hide_name_tag,
                skin=skin,
                equipment=equipment,
            ),
        )

        if on_click is not None:
            _reject_click_conflict(
                name,
                on_left_click=on_left_click,
                on_right_click=on_right_click,
                left_click_redirect=left_click_redirect,
            )
            self.attach('both', on_click)
        if on_left_click is not None:
            self.attach('left', on_left_click)
        if on_right_click is not None:
            self.attach('right', on_right_click)

    @property
    def declared(self) -> NpcImportable:
        importable = self.declaration()
        assert isinstance(importable, NpcImportable)
        return importable

    def attach(self, which: Which, handler: Handler) -> None:
        """Give this NPC a click handler after the fact.

        `'both'` is `on_click`: it fills the right-click list and turns
        `leftClickRedirect` on, because Housing has no "either button" list of
        its own - a left click has to be pointed at the right-click one."""
        name = self.name
        importable = self.declared

        if which == 'both':
            _reject_click_conflict(
                name,
                on_left_click=importable.left,
                on_right_click=importable.right,
                left_click_redirect=importable.left_click_redirect,
            )
            self.__click_mode__ = 'both'
            importable.right = self._make_block(name, 'right', handler)
            importable.left_click_redirect = True
            return

        if self.__click_mode__ == 'both':
            raise ValueError(
                f'NPC "{name}": on_click already covers both buttons, so a '
                f'separate {which}-click handler would never run.',
            )
        if which == 'left':
            importable.left = self._make_block(name, 'left', handler)
        else:
            importable.right = self._make_block(name, 'right', handler)

    def _make_block(self, name: str, side: str, handler: Handler) -> NamedBlock:
        block = NamedBlock(
            f'{name} {side}',
            callback=lambda: call_with_args(handler, self),
            importable_kind='npcs',
        )
        get_current_container().add_block(block)
        return block

    def left_click(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """`@npc.left_click` - run these actions on a left click."""
        self.attach('left', func)
        return func

    def right_click(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """`@npc.right_click` - run these actions on a right click."""
        self.attach('right', func)
        return func

    def click(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """`@npc.click` - run these actions on either button."""
        self.attach('both', func)
        return func


@overload
def create_npc(
    name: str,
    pos: Coord,
    *,
    on_click: Handler,
    look_at_players: bool | None = ...,
    hide_name_tag: bool | None = ...,
    skin: NpcSkin | None = ...,
    equipment: NpcEquipment | None = ...,
) -> NPC: ...


@overload
def create_npc(
    name: str,
    pos: Coord,
    *,
    on_left_click: Handler | None = ...,
    on_right_click: Handler | None = ...,
    left_click_redirect: bool | None = ...,
    look_at_players: bool | None = ...,
    hide_name_tag: bool | None = ...,
    skin: NpcSkin | None = ...,
    equipment: NpcEquipment | None = ...,
) -> NPC: ...


def create_npc(
    name: str,
    pos: Coord,
    *,
    on_click: Handler | None = None,
    on_left_click: Handler | None = None,
    on_right_click: Handler | None = None,
    left_click_redirect: bool | None = None,
    look_at_players: bool | None = None,
    hide_name_tag: bool | None = None,
    skin: NpcSkin | None = None,
    equipment: NpcEquipment | None = None,
) -> NPC:
    """Declare an NPC and return it, so NPCs can be built by a function called
    in a loop. `on_click` and the left/right pair are mutually exclusive - the
    overloads make passing both a type error, and it is rejected at runtime."""
    return NPC(
        name,
        pos,
        on_click=on_click,
        on_left_click=on_left_click,
        on_right_click=on_right_click,
        left_click_redirect=left_click_redirect,
        look_at_players=look_at_players,
        hide_name_tag=hide_name_tag,
        skin=skin,
        equipment=equipment,
    )
