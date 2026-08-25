from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with

from ..expression.expression import Expression

__all__ = (
    'FailParkourExpression',
    'fail_parkour',
)


@final
class FailParkourExpression(Expression):
    reason: str

    def __init__(self, reason: str = 'Failed!') -> None:
        self.reason = reason

    def into_htsl(self) -> str:
        return f'failParkour {self.inline_quoted(self.reason)}'

    def cloned(
        self,
        *,
        reason: str | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'reason': reason,
            },
        )

    def equals(self, other: object) -> bool:
        if not isinstance(other, FailParkourExpression):
            return False
        return self.reason == other.reason

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.reason}>'


def fail_parkour(reason: str = 'Failed!') -> None:
    FailParkourExpression(reason=reason).write()
