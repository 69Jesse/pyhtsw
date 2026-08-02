from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyhtsw.importable import CommandImportable


__all__ = ('Command',)


class Command:
    """A custom `/command` importable. Unlike a Function it is not callable
    from HTSL — Housing has no trigger-command action — so this only carries
    the name for reference and reexport."""

    name: str
    __htsw_importable__: 'CommandImportable'

    def __init__(self, name: str) -> None:
        self.name = name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Command):
            return NotImplemented
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.name}>'
