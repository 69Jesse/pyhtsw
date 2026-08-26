from typing import final

from pyhtsw.expression.expression import Expression
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

__all__ = (
    'ResetInventoryExpression',
    'reset_inventory',
)


@final
class ResetInventoryExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='RESET_INVENTORY',
        limit=1,
        effects=Effects.of(writes=(Resource.INVENTORY,)),
        display_name='Reset Inventory',
        forbidden_events=('Player Quit',),
    )

    def into_htsl(self) -> str:
        return 'resetInventory'


def reset_inventory() -> None:
    ResetInventoryExpression().write()
