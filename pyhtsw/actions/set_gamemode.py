from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with

from ..expression.expression import Expression
from ..types import ALL_GAMEMODES

__all__ = (
    'SetGamemodeExpression',
    'set_gamemode',
)


@final
class SetGamemodeExpression(Expression):
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

    def equals(self, other: object) -> bool:
        if not isinstance(other, SetGamemodeExpression):
            return False
        return self.gamemode == other.gamemode

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.gamemode}>'


def set_gamemode(gamemode: ALL_GAMEMODES) -> None:
    SetGamemodeExpression(gamemode=gamemode).write()
