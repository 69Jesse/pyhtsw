from typing import ClassVar

from .condition import Condition

__all__ = ('NamedCondition',)


class NamedCondition(Condition):
    name: str
    # Subclasses (PlayerSneaking, ...) hardcode their name with a no-arg
    # __init__, so it has to survive as an extra rather than a field.
    __clone_extra__: ClassVar[tuple[str, ...]] = ('name',)

    def __init__(
        self,
        name: str,
    ) -> None:
        self.name = name

    def into_htsl_raw(self) -> str:
        return self.name

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, NamedCondition):
            return False
        return self.name == other.name

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.name} inverted={self.inverted}>'
