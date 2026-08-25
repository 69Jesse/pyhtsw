from typing import final

from ..expression.expression import Expression

__all__ = (
    'KillPlayerExpression',
    'kill_player',
)


@final
class KillPlayerExpression(Expression):
    def into_htsl(self) -> str:
        return 'kill'

    def equals(self, other: object) -> bool:
        return isinstance(other, KillPlayerExpression)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}'


def kill_player() -> None:
    KillPlayerExpression().write()
