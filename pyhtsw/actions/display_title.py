from typing import TYPE_CHECKING, Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.utils.formatting import formatting_to_ansi
from pyhtsw.utils.log import log

from ..checkable import Checkable
from ..expression.expression import Expression
from ..expression.housing_type import HousingType

if TYPE_CHECKING:
    from ..execute.context import ExecutionContext

__all__ = (
    'DisplayTitleExpression',
    'display_title',
)


@final
class DisplayTitleExpression(Expression):
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
