from collections.abc import Callable
from types import MethodType
from typing import Any, Literal, overload

from ..block import NamedBlock
from ..container import get_current_container
from ..importable import (
    Coord,
    Handler,
    NpcEquipment,
    NpcImportable,
    NpcSkin,
    call_with_args,
)
from ..utils.caller import caller_module
from .item import click, left_click, right_click

__all__ = ('NPC', 'create_npc')

Which = Literal['left', 'right', 'both']

_TAGGERS: dict[Which, Callable[[Callable[[], None]], Callable[[], None]]] = {
    'left': left_click,
    'right': right_click,
    'both': click,
}


class _Click:
    which: Which

    def __init__(self, which: Which) -> None:
        self.which = which

    def __get__(self, obj: 'NPC | None', cls: type | None = None) -> Any:
        if obj is None:
            return _TAGGERS[self.which]

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            obj.attach(self.which, func)
            return func

        return decorator


class _NpcMethod:
    def __init__(self, func: Callable[..., Any]) -> None:
        self.func = func
        self.__doc__ = func.__doc__

    def __get__(self, obj: Any, cls: type | None = None) -> Any:
        return MethodType(self.func, cls if obj is None else obj)


def _reject_click_conflict(name: str, **present: object) -> None:
    conflicting = [label for label, value in present.items() if value is not None]
    if conflicting:
        raise ValueError(
            f'NPC "{name}": on_click already means "right-click actions, and '
            f'left click redirects to them", so it cannot be combined with '
            f'{", ".join(sorted(conflicting))}.',
        )


class NPC:
    Equipment = NpcEquipment

    __htsw_name__: 'str | None' = None
    __htsw_importable__: 'NpcImportable'
    __htsw_click_mode__: 'Which | None' = None

    left_click = _Click('left')
    right_click = _Click('right')
    click = _Click('both')

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
        """Declare an NPC as a value rather than a subclass. Prefer
        `create_npc(...)`, which is the same thing under a name matching
        `create_function` and friends."""
        self.__htsw_name__ = name
        importable = NpcImportable(
            name=name,
            pos=pos,
            left_click_redirect=left_click_redirect,
            look_at_players=look_at_players,
            hide_name_tag=hide_name_tag,
            skin=skin,
            equipment=equipment,
        )
        importable.module = caller_module()
        self.__htsw_importable__ = importable
        get_current_container().register_importable(importable)

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

    def __repr__(self) -> str:
        return f'{type(self).__name__}<{self.__htsw_name__}>'

    def __init_subclass__(
        cls,
        name: str,
        pos: Coord,
        on_click: Handler | None = None,
        on_left_click: Handler | None = None,
        on_right_click: Handler | None = None,
        left_click_redirect: bool | None = None,
        look_at_players: bool | None = None,
        hide_name_tag: bool | None = None,
        skin: NpcSkin | None = None,
        equipment: NpcEquipment | None = None,
    ) -> None:
        super().__init_subclass__()
        cls.__htsw_name__ = name
        cls.__htsw_click_mode__ = None

        for value in vars(cls).values():
            tag = getattr(value, '__htsw_click__', None)
            if tag == 'left':
                on_left_click = value
            elif tag == 'right':
                on_right_click = value
            elif tag == 'both':
                on_click = value

        if on_click is not None:
            _reject_click_conflict(
                name,
                on_left_click=on_left_click,
                on_right_click=on_right_click,
                left_click_redirect=left_click_redirect,
            )

        importable = NpcImportable(
            name=name,
            pos=pos,
            left_click_redirect=left_click_redirect,
            look_at_players=look_at_players,
            hide_name_tag=hide_name_tag,
            skin=skin,
            equipment=equipment,
        )
        importable.module = caller_module()
        cls.__htsw_importable__ = importable
        get_current_container().register_importable(importable)

        if on_click is not None:
            cls.attach('both', on_click)
        if on_left_click is not None:
            cls.attach('left', on_left_click)
        if on_right_click is not None:
            cls.attach('right', on_right_click)

    @_NpcMethod
    def attach(self, which: Which, handler: Handler) -> None:
        """Give this NPC a click handler after the fact.

        `'both'` is `on_click`: it fills the right-click list and turns
        `leftClickRedirect` on, because Housing has no "either button" list of
        its own — a left click has to be pointed at the right-click one."""
        name = self.__htsw_name__ or '?'
        importable = self.__htsw_importable__

        if which == 'both':
            _reject_click_conflict(
                name,
                on_left_click=importable.left,
                on_right_click=importable.right,
                left_click_redirect=importable.left_click_redirect,
            )
            self.__htsw_click_mode__ = 'both'
            importable.right = self._make_block(name, 'right', handler)
            importable.left_click_redirect = True
            return

        if self.__htsw_click_mode__ == 'both':
            raise ValueError(
                f'NPC "{name}": on_click already covers both buttons, so a '
                f'separate {which}-click handler would never run.',
            )
        if which == 'left':
            importable.left = self._make_block(name, 'left', handler)
        else:
            importable.right = self._make_block(name, 'right', handler)

    @_NpcMethod
    def _make_block(self, name: str, side: str, handler: Handler) -> NamedBlock:
        owner = self
        block = NamedBlock(
            f'{name} {side}',
            callback=lambda: call_with_args(handler, owner),
            importable_kind='npcs',
        )
        get_current_container().add_block(block)
        return block


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
    in a loop instead of by a class statement. `on_click` and the
    left/right pair are mutually exclusive — the overloads make passing both a
    type error, and it is rejected at runtime too."""
    npc = NPC(
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
    npc.__htsw_importable__.module = caller_module()
    return npc
