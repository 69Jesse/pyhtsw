from typing import ClassVar, Self

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.expression.condition.condition import Condition

__all__ = ('NamedCondition',)


class NamedCondition(Condition):
    name: str
    # Subclasses (IsSneakingCondition, ...) hardcode their name with a no-arg
    # __init__, so it has to survive as an extra rather than a field.
    __clone_extra__: ClassVar[tuple[str, ...]] = ('name',)

    def __init__(
        self,
        name: str,
    ) -> None:
        self.name = name

    def into_htsl_raw(self) -> str:
        return self.name

    def cloned(
        self,
        *,
        name: str | Missing = MISSING,
        inverted: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'name': name,
                'inverted': inverted,
            },
        )

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, NamedCondition):
            return False
        return self.name == other.name

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.name} inverted={self.inverted}>'
