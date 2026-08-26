from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

from ..expression.expression import Expression

__all__ = (
    'ToggleNametagDisplayExpression',
    'toggle_nametag_display',
)


@final
class ToggleNametagDisplayExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='TOGGLE_NAMETAG_DISPLAY',
        limit=5,
        effects=Effects.of(writes=(Resource.NAMETAG,)),
        display_name='Toggle Nametag Display',
        forbidden_events=('Player Quit',),
    )

    display: bool

    def __init__(self, display: bool) -> None:
        self.display = display

    def into_htsl(self) -> str:
        return f'displayNametag {self.inline(self.display)}'

    def cloned(
        self,
        *,
        display: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'display': display,
            },
        )


def toggle_nametag_display(display: bool) -> None:
    ToggleNametagDisplayExpression(display=display).write()
