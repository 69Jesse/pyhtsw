from typing import TYPE_CHECKING, Self, final

from pyhtsw.clone import MISSING, Missing, clone_with

from .expression import Expression

if TYPE_CHECKING:
    from ..execute.context import ExecutionContext
    from ..stats.stat import Stat


@final
class UnsetExpression(Expression):
    target: 'Stat'

    def __init__(self, target: 'Stat') -> None:
        self.target = target

    def cloned(
        self,
        *,
        target: 'Stat | Missing' = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'target': target,
            },
        )

    def equals(self, other: object) -> bool:
        if not isinstance(other, UnsetExpression):
            return False
        return self.target.equals(other.target)

    def into_htsl(self) -> str:
        return f'{self.target.into_string_lhs()} unset'

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{repr(self.target)}>'

    def raw_execute(self, context: 'ExecutionContext') -> None:
        context.pop(self.target)
