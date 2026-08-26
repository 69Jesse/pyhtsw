from types import MappingProxyType
from typing import TYPE_CHECKING

from .declaration import resolve_declaration

if TYPE_CHECKING:
    from collections.abc import Mapping

    from ..importable import GroupImportable
    from ..types import (
        ALL_CHAT_SPEEDS,
        ALL_DEFAULT_GAMEMODES,
        ALL_HOUSING_COLORS,
        ALL_PERMISSIONS,
    )


__all__ = ('Group',)


class Group:
    name: str
    # Set by create_group; None for a plain reference to a group declared
    # elsewhere (or in-game).
    __htsw_importable__: 'GroupImportable | None' = None

    def __init__(self, name: str) -> None:
        self.name = name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Group):
            return NotImplemented
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def _declaration(self, field: str) -> 'GroupImportable':
        from ..importable import GroupImportable

        return resolve_declaration(
            self.__htsw_importable__,
            GroupImportable,
            self.name,
            field,
            'create_group',
        )

    @property
    def tag(self) -> str | None:
        return self._declaration('tag').tag

    @property
    def tag_shown_in_chat(self) -> bool | None:
        return self._declaration('tag_shown_in_chat').tag_shown_in_chat

    @property
    def color(self) -> 'ALL_HOUSING_COLORS | None':
        return self._declaration('color').color

    @property
    def priority(self) -> int | None:
        return self._declaration('priority').priority

    @property
    def permissions(self) -> 'Mapping[ALL_PERMISSIONS, bool] | None':
        permissions = self._declaration('permissions').permissions
        return None if permissions is None else MappingProxyType(permissions)

    @property
    def chat_speed(self) -> 'ALL_CHAT_SPEEDS | None':
        return self._declaration('chat_speed').chat_speed

    @property
    def default_gamemode(self) -> 'ALL_DEFAULT_GAMEMODES | None':
        return self._declaration('default_gamemode').default_gamemode
