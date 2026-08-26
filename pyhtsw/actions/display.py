from typing import TYPE_CHECKING, ClassVar, Self, final

from pyhtsw.checkable import Checkable
from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.compiler.registry import ActionMeta
from pyhtsw.compiler.schedule import Effects, Resource, Stream
from pyhtsw.declarations.menu import Menu
from pyhtsw.expression.expression import Expression
from pyhtsw.expression.housing_type import HousingType
from pyhtsw.utils.formatting import formatting_to_ansi
from pyhtsw.utils.log import log

__all__ = (
    'ChatExpression',
    'chat',
    'DisplayTitleExpression',
    'display_title',
    'DisplayActionBarExpression',
    'display_action_bar',
    'DisplayMenuExpression',
    'display_menu',
    'CloseMenuExpression',
    'close_menu',
)

if TYPE_CHECKING:
    from pyhtsw.execute.context import ExecutionContext


@final
class ChatExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='MESSAGE',
        limit=20,
        effects=Effects.of(stream=Stream.TEXT),
        display_name='Send a Chat Message',
        forbidden_events=('player_quit',),
    )

    line: str

    def __init__(self, line: str) -> None:
        self.line = line

    def into_htsl(self) -> str:
        return f'chat {self.inline_quoted(self.line)}'

    def raw_execute(self, context: 'ExecutionContext') -> None:
        log(
            formatting_to_ansi(
                f'&7* &f{context.get(self.line, cast=False, output="string")}',
            ),
        )

    def cloned(
        self,
        *,
        line: str | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'line': line,
            },
        )


def chat(line: str) -> None:
    ChatExpression(line=line).write()


if TYPE_CHECKING:
    from pyhtsw.execute.context import ExecutionContext


@final
class DisplayTitleExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='TITLE',
        limit=5,
        effects=Effects.of(stream=Stream.TEXT),
        display_name='Display Title',
        forbidden_events=('player_quit',),
    )

    title: Checkable | str
    subtitle: Checkable | str
    fadein: int
    stay: int
    fadeout: int

    def __init__(
        self,
        title: Checkable | str,
        subtitle: Checkable | str,
        fadein: int = 1,
        stay: int = 5,
        fadeout: int = 1,
    ) -> None:
        self.title = title
        self.subtitle = subtitle
        self.fadein = fadein
        self.stay = stay
        self.fadeout = fadeout

    def into_htsl(self) -> str:
        return (
            f'title {self.inline_quoted(self.title)} {self.inline_quoted(self.subtitle)}'
            f' {self.inline(self.fadein)} {self.inline(self.stay)} {self.inline(self.fadeout)}'
        )

    def raw_execute(self, context: 'ExecutionContext') -> None:
        log(
            formatting_to_ansi(
                '&7<display-title>\n'
                f'&7    title: &f{context.get(self.title, cast=False, output="string")}\n'
                f'&7    subtitle: &f{context.get(self.subtitle, cast=False, output="string")}\n'
                f'&7    fadein: &f{self.fadein}\n'
                f'&7    stay: &f{self.stay}\n'
                f'&7    fadeout: &f{self.fadeout}',
            ),
        )

    def cloned(
        self,
        *,
        title: Checkable | str | Missing = MISSING,
        subtitle: Checkable | str | Missing = MISSING,
        fadein: int | Missing = MISSING,
        stay: int | Missing = MISSING,
        fadeout: int | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'title': title,
                'subtitle': subtitle,
                'fadein': fadein,
                'stay': stay,
                'fadeout': fadeout,
            },
        )


def display_title(
    title: Checkable | str | None = None,
    subtitle: Checkable | str | None = None,
    fadein: int = 1,
    stay: int = 5,
    fadeout: int = 1,
) -> None:
    resolved_title: Checkable | HousingType = title if title is not None else '&r'
    resolved_subtitle: Checkable | HousingType = (
        subtitle if subtitle is not None else '&r'
    )
    DisplayTitleExpression(
        title=resolved_title,
        subtitle=resolved_subtitle,
        fadein=fadein,
        stay=stay,
        fadeout=fadeout,
    ).write()


if TYPE_CHECKING:
    from pyhtsw.execute.context import ExecutionContext


@final
class DisplayActionBarExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='ACTION_BAR',
        limit=5,
        effects=Effects.of(stream=Stream.TEXT),
        display_name='Display Action Bar',
        forbidden_events=('player_quit',),
    )

    text: Checkable | str

    def __init__(self, text: Checkable | str) -> None:
        self.text = text

    def into_htsl(self) -> str:
        return f'actionBar {self.inline_quoted(self.text)}'

    def raw_execute(self, context: 'ExecutionContext') -> None:
        log(
            formatting_to_ansi(
                '&7<display-action-bar>\n'
                f'&7    text: &f{context.get(self.text, cast=False, output="string")}',
            ),
        )

    def cloned(
        self,
        *,
        text: Checkable | str | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'text': text,
            },
        )


def display_action_bar(
    text: Checkable | str | None = None,
) -> None:
    resolved: Checkable | HousingType = text if text is not None else '&r'
    DisplayActionBarExpression(text=resolved).write()


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
        forbidden_events=('player_quit',),
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
