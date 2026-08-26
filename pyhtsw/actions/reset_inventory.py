from typing import final

from ..expression.expression import Expression

__all__ = (
    'ResetInventoryExpression',
    'reset_inventory',
)


@final
class ResetInventoryExpression(Expression):
    def into_htsl(self) -> str:
        return 'resetInventory'


def reset_inventory() -> None:
    ResetInventoryExpression().write()
