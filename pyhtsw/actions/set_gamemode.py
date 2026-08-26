from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

from ..expression.expression import Expression
from ..types import ALL_GAMEMODES

__all__ = (
    'SetGamemodeExpression',
    'set_gamemode',
)


@final
class SetGamemodeExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='SET_GAMEMODE',
        limit=1,
        effects=Effects.of(writes=(Resource.GAMEMODE,)),
        display_name='Set Gamemode',
        forbidden_events=('Player Quit',),
    )

    gamemode: ALL_GAMEMODES

    def __init__(self, gamemode: ALL_GAMEMODES) -> None:
        self.gamemode = gamemode

    def into_htsl(self) -> str:
        return f'gamemode {self.inline(self.gamemode)}'

    def cloned(
        self,
        *,
        gamemode: ALL_GAMEMODES | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'gamemode': gamemode,
            },
        )


def set_gamemode(gamemode: ALL_GAMEMODES) -> None:
    SetGamemodeExpression(gamemode=gamemode).write()
