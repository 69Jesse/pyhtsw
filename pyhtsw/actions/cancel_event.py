from typing import final

from ..expression.expression import Expression

__all__ = (
    'CancelEventExpression',
    'cancel_event',
)


@final
class CancelEventExpression(Expression):
    def into_htsl(self) -> str:
        return 'cancelEvent'


def cancel_event() -> None:
    CancelEventExpression().write()
