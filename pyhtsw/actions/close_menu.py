from typing import final

from ..expression.expression import Expression

__all__ = (
    'CloseMenuExpression',
    'close_menu',
)


@final
class CloseMenuExpression(Expression):
    def into_htsl(self) -> str:
        return 'closeMenu'


def close_menu() -> None:
    CloseMenuExpression().write()
