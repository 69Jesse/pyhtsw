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


def apply_inventory_layout(layout: Layout | str) -> None:
    layout = layout if isinstance(layout, Layout) else Layout(layout)
    ApplyInventoryLayoutExpression(layout=layout).write()
