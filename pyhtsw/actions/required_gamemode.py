from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with

from ..expression.condition.condition import Condition
from ..types import ALL_GAMEMODES

__all__ = ('RequiredGamemode',)


@final
class RequiredGamemode(Condition):
    gamemode: ALL_GAMEMODES

    def __init__(
        self,
        gamemode: ALL_GAMEMODES,
    ) -> None:
        self.gamemode = gamemode

    def into_htsl_raw(self) -> str:
        return f'gamemode {self.inline(self.gamemode)}'

    def cloned(
        self,
        *,
        gamemode: ALL_GAMEMODES | Missing = MISSING,
        inverted: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'gamemode': gamemode,
                'inverted': inverted,
            },
        )
