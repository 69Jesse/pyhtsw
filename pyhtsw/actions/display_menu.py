from typing import ClassVar, Self, final

from pyhtsw.clone import MISSING, Missing, clone_with

from ..expression.expression import Expression
from .menu import Menu

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
