from collections.abc import Mapping, Sequence

from ..container import get_current_container
from ..importable import GroupImportable
from ..types import (
    ALL_CHAT_SPEEDS,
    ALL_DEFAULT_GAMEMODES,
    ALL_HOUSING_COLORS,
    ALL_PERMISSIONS,
)
from ..utils.caller import caller_module
from .group import Group

__all__ = ('create_group',)


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


def create_group(
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
) -> Group:
    """Declare a group importable and return the `Group` that
    `change_player_group` and `RequiredGroup` already take."""
    importable = GroupImportable(
        name=name,
        tag=tag,
        tag_shown_in_chat=tag_shown_in_chat,
        color=color,
        priority=priority,
        permissions=_merge_permissions(name, allow, deny, permissions),
        chat_speed=chat_speed,
        default_gamemode=default_gamemode,
    )
    importable.module = caller_module()
    get_current_container().register_importable(importable)

    group = Group(name)
    group.__htsw_importable__ = importable
    return group
