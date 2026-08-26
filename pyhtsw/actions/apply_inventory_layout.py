from typing import Self, final

from pyhtsw.actions.layout import Layout
from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.expression.expression import Expression
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

__all__ = (
    'ApplyInventoryLayoutExpression',
    'apply_inventory_layout',
)


@final
class ApplyInventoryLayoutExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='APPLY_INVENTORY_LAYOUT',
        limit=5,
        effects=Effects.of(writes=(Resource.INVENTORY,)),
        display_name='Apply Inventory Layout',
        forbidden_events=('Player Quit',),
    )

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
