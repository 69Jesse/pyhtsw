from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import TYPE_CHECKING

from pyhtsw.compiler.importable import GroupImportable
from pyhtsw.declarations.declared import Declared, declared_field, register_importable
from pyhtsw.generated.enums import (
    ChatSpeed,
    Gamemode,
    HousingColor,
    Permission,
)

__all__ = ('Group',)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pyhtsw.generated.enums import (
        ChatSpeed,
        Gamemode,
        HousingColor,
        Permission,
    )


def _permissions_view(
    permissions: 'dict[Permission, bool] | None',
) -> 'Mapping[Permission, bool] | None':
    return None if permissions is None else MappingProxyType(permissions)


class Group(Declared):
    __htsw_kind__ = 'groups'
    __htsw_factory__ = 'Group'

    tag: declared_field[str | None] = declared_field()
    tag_shown_in_chat: declared_field[bool | None] = declared_field()
    color: 'declared_field[HousingColor | None]' = declared_field()
    priority: declared_field[int | None] = declared_field()
    permissions: 'declared_field[Mapping[Permission, bool] | None]' = declared_field(
        transform=_permissions_view,
        readonly=True,
    )
    chat_speed: 'declared_field[ChatSpeed | None]' = declared_field()
    default_gamemode: 'declared_field[Gamemode | None]' = declared_field()

    def __init__(
        self,
        name: str,
        *,
        tag: str | None = None,
        tag_shown_in_chat: bool | None = None,
        color: HousingColor | None = None,
        priority: int | None = None,
        allow: Sequence[Permission] | None = None,
        deny: Sequence[Permission] | None = None,
        permissions: Mapping[Permission, bool] | None = None,
        chat_speed: ChatSpeed | None = None,
        default_gamemode: Gamemode | None = None,
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
    allow: Sequence[Permission] | None,
    deny: Sequence[Permission] | None,
    permissions: Mapping[Permission, bool] | None,
) -> dict[Permission, bool] | None:
    merged: dict[Permission, bool] = dict(permissions or {})
    for permission in allow or ():
        merged[permission] = True
    for permission in deny or ():
        if permission in (allow or ()):
            raise ValueError(
                f'Group "{name}": permission {permission!r} is in both allow and deny.',
            )
        merged[permission] = False
    return merged or None
