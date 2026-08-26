from typing import final

from pyhtsw.expression.expression import Expression
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

__all__ = (
    'CloseMenuExpression',
    'close_menu',
)


@final
class CloseMenuExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='CLOSE_MENU',
        limit=1,
        effects=Effects.of(writes=(Resource.MENU,)),
        display_name='Close Menu',
        menu_only=True,
    )

    def into_htsl(self) -> str:
        return 'closeMenu'


def close_menu() -> None:
    CloseMenuExpression().write()
