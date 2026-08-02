from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..importable import GroupImportable


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
