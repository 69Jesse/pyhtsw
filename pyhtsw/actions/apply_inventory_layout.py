from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with

from ..expression.expression import Expression
from .layout import Layout

__all__ = (
    'ApplyInventoryLayoutExpression',
    'apply_inventory_layout',
)


@final
class ApplyInventoryLayoutExpression(Expression):
    layout: Layout

    def __init__(self, layout: Layout) -> None:
        self.layout = layout

    def into_htsl(self) -> str:
        return f'applyLayout {self.inline_quoted(self.layout.name)}'

    def cloned(
        self,
        *,
        layout: Layout | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'layout': layout,
            },
        )

    def equals(self, other: object) -> bool:
        if not isinstance(other, ApplyInventoryLayoutExpression):
            return False
        return self.layout.name == other.layout.name

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.layout.name}>'


def apply_inventory_layout(layout: Layout | str) -> None:
    layout = layout if isinstance(layout, Layout) else Layout(layout)
    ApplyInventoryLayoutExpression(layout=layout).write()
