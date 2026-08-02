from typing import Self, final

from ..expression.expression import Expression

__all__ = (
    'ToggleNametagDisplayExpression',
    'toggle_nametag_display',
)


@final
class ToggleNametagDisplayExpression(Expression):
    display: bool

    def __init__(self, display: bool) -> None:
        self.display = display

    def into_htsl(self) -> str:
        return f'displayNametag {self.inline(self.display)}'

    def cloned(self) -> Self:
        return self.__class__(display=self.display)

    def equals(self, other: object) -> bool:
        if not isinstance(other, ToggleNametagDisplayExpression):
            return False
        return self.display == other.display

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.display}>'


def toggle_nametag_display(display: bool) -> None:
    ToggleNametagDisplayExpression(display=display).write()
