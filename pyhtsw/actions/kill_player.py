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


def kill_player() -> None:
    KillPlayerExpression().write()
