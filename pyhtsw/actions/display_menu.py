from typing import ClassVar, Self, final

from pyhtsw.actions.menu import Menu
from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.expression.expression import Expression
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

__all__ = (
    'DisplayMenuExpression',
    'display_menu',
)


def _menu_name(menu: 'Menu | str') -> str:
    if isinstance(menu, str):
        return menu
    if isinstance(menu, Menu):
        return menu.name
    raise TypeError(f'Expected a Menu or str, got {menu!r}')


@final
class DisplayMenuExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='SET_MENU',
        limit=10,
        effects=Effects.of(writes=(Resource.MENU,)),
        display_name='Display Menu',
        forbidden_events=('Player Quit',),
    )

    name: str
    __clone_map__: ClassVar[dict[str, str]] = {'menu': 'name'}

    def __init__(self, menu: 'Menu | str') -> None:
        self.name = _menu_name(menu)

    def into_htsl(self) -> str:
        return f'displayMenu {self.inline_quoted(self.name)}'

    def referenced_importables(self) -> list[tuple[str, str]]:
        return [('menus', self.name)]

    def cloned(
        self,
        *,
        menu: 'Menu | str | Missing' = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'menu': menu,
            },
        )


def display_menu(menu: 'Menu | str') -> None:
    DisplayMenuExpression(menu=menu).write()
