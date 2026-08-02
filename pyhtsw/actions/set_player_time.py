from typing import ClassVar, Self, final

from ..expression.expression import Expression

__all__ = (
    'PlayerTime',
    'SetPlayerTimeExpression',
    'set_player_time',
)


class PlayerTime:
    """The four presets Housing's selector offers. Any other tick value in
    [0, 24000) is accepted too."""

    SUNRISE: ClassVar[int] = 0
    NOON: ClassVar[int] = 6000
    SUNSET: ClassVar[int] = 12000
    MIDNIGHT: ClassVar[int] = 18000


@final
class SetPlayerTimeExpression(Expression):
    time: int

    def __init__(self, time: int) -> None:
        self.time = time

    def into_htsl(self) -> str:
        return f'playerTime {self.inline(self.time)}'

    def cloned(self) -> Self:
        return self.__class__(time=self.time)

    def equals(self, other: object) -> bool:
        if not isinstance(other, SetPlayerTimeExpression):
            return False
        return self.time == other.time

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.time}>'


def set_player_time(time: int) -> None:
    # htsw types this field as a plain bounded number, so a stat/placeholder
    # would emit something `htsw check` rejects.
    if not isinstance(time, int) or isinstance(time, bool):
        raise TypeError(
            f'set_player_time expects a whole number of ticks, got {time!r}.',
        )
    if not 0 <= time <= 23999:
        raise ValueError(f'set_player_time: {time} is outside the range 0-23999.')
    SetPlayerTimeExpression(time=time).write()
