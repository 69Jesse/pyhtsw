from types import MappingProxyType
from typing import TYPE_CHECKING

from pyhtsw.declared import Declared, declared_field

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pyhtsw.types import (
        ALL_CHAT_SPEEDS,
        ALL_DEFAULT_GAMEMODES,
        ALL_HOUSING_COLORS,
        ALL_PERMISSIONS,
    )


__all__ = ('Group',)


def _permissions_view(
    permissions: 'dict[ALL_PERMISSIONS, bool] | None',
) -> 'Mapping[ALL_PERMISSIONS, bool] | None':
    return None if permissions is None else MappingProxyType(permissions)


class Group(Declared):
    __htsw_kind__ = 'groups'
    __htsw_factory__ = 'create_group'

    tag: declared_field[str | None] = declared_field()
    tag_shown_in_chat: declared_field[bool | None] = declared_field()
    color: 'declared_field[ALL_HOUSING_COLORS | None]' = declared_field()
    priority: declared_field[int | None] = declared_field()
    permissions: 'declared_field[Mapping[ALL_PERMISSIONS, bool] | None]' = (
        declared_field(transform=_permissions_view, readonly=True)
    )
    chat_speed: 'declared_field[ALL_CHAT_SPEEDS | None]' = declared_field()
    default_gamemode: 'declared_field[ALL_DEFAULT_GAMEMODES | None]' = declared_field()
