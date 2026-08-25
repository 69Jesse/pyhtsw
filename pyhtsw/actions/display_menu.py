from typing import ClassVar, Self, final

from pyhtsw.clone import MISSING, Missing, clone_with

from ..expression.expression import Expression
from .menu import Menu

__all__ = (
    'DisplayMenuExpression',
    'display_menu',
)


def _menu_name(menu: 'type[Menu] | str') -> str:
    if isinstance(menu, str):
        return menu
    if isinstance(menu, type) and issubclass(menu, Menu):
        return menu.__htsw_name__ or menu.__name__
    raise TypeError(f'Expected a Menu subclass or str, got {menu!r}')


@final
class DisplayMenuExpression(Expression):
    name: str
    __clone_map__: ClassVar[dict[str, str]] = {'menu': 'name'}

    def __init__(self, menu: 'type[Menu] | str') -> None:
        self.name = _menu_name(menu)

    def into_htsl(self) -> str:
        return f'displayMenu {self.inline_quoted(self.name)}'

    def referenced_importables(self) -> list[tuple[str, str]]:
        return [('menus', self.name)]

    def cloned(
        self,
        *,
        menu: 'type[Menu] | str | Missing' = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'menu': menu,
            },
        )

    def equals(self, other: object) -> bool:
        if not isinstance(other, DisplayMenuExpression):
            return False
        return self.name == other.name

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.name}>'


def display_menu(menu: 'type[Menu] | str') -> None:
    DisplayMenuExpression(menu=menu).write()
