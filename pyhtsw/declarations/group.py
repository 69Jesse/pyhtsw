from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import TYPE_CHECKING

from pyhtsw.types import (
    ALL_CHAT_SPEEDS,
    ALL_DEFAULT_GAMEMODES,
    ALL_HOUSING_COLORS,
    ALL_PERMISSIONS,
)

from pyhtsw.compiler.importable import GroupImportable
from pyhtsw.declarations.declared import Declared, declared_field, register_importable

__all__ = ('Group',)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pyhtsw.types import (
        ALL_CHAT_SPEEDS,
        ALL_DEFAULT_GAMEMODES,
        ALL_HOUSING_COLORS,
        ALL_PERMISSIONS,
    )


def _permissions_view(
    permissions: 'dict[ALL_PERMISSIONS, bool] | None',
) -> 'Mapping[ALL_PERMISSIONS, bool] | None':
    return None if permissions is None else MappingProxyType(permissions)


class Group(Declared):
    __htsw_kind__ = 'groups'
    __htsw_factory__ = 'Group'

    tag: declared_field[str | None] = declared_field()
    tag_shown_in_chat: declared_field[bool | None] = declared_field()
    color: 'declared_field[ALL_HOUSING_COLORS | None]' = declared_field()
    priority: declared_field[int | None] = declared_field()
    permissions: 'declared_field[Mapping[ALL_PERMISSIONS, bool] | None]' = (
        declared_field(transform=_permissions_view, readonly=True)
    )
    chat_speed: 'declared_field[ALL_CHAT_SPEEDS | None]' = declared_field()
    default_gamemode: 'declared_field[ALL_DEFAULT_GAMEMODES | None]' = declared_field()

    def __init__(
        self,
        name: str,
        *,
        tag: str | None = None,
        tag_shown_in_chat: bool | None = None,
        color: ALL_HOUSING_COLORS | None = None,
        priority: int | None = None,
        allow: Sequence[ALL_PERMISSIONS] | None = None,
        deny: Sequence[ALL_PERMISSIONS] | None = None,
        permissions: Mapping[ALL_PERMISSIONS, bool] | None = None,
        chat_speed: ALL_CHAT_SPEEDS | None = None,
        default_gamemode: ALL_DEFAULT_GAMEMODES | None = None,
    ) -> None:
        """Declare a group importable. A group that already exists in the house
        is referenced by its plain name instead."""
        super().__init__(name)
        self.__htsw_importable__ = register_importable(
            GroupImportable(
                name=name,
                tag=tag,
                tag_shown_in_chat=tag_shown_in_chat,
                color=color,
                priority=priority,
                permissions=_merge_permissions(name, allow, deny, permissions),
                chat_speed=chat_speed,
                default_gamemode=default_gamemode,
            ),
        )


def _merge_permissions(
    name: str,
    allow: Sequence[ALL_PERMISSIONS] | None,
    deny: Sequence[ALL_PERMISSIONS] | None,
    permissions: Mapping[ALL_PERMISSIONS, bool] | None,
) -> dict[ALL_PERMISSIONS, bool] | None:
    merged: dict[ALL_PERMISSIONS, bool] = dict(permissions or {})
    for permission in allow or ():
        merged[permission] = True
    for permission in deny or ():
        if permission in (allow or ()):
            raise ValueError(
                f'Group "{name}": permission {permission!r} is in both allow and deny.',
            )
        merged[permission] = False
    return merged or None
