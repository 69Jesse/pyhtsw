from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with

from ..expression.expression import Expression
from ..types import PLAYER_WEATHERS

__all__ = (
    'SetPlayerWeatherExpression',
    'set_player_weather',
)


@final
class SetPlayerWeatherExpression(Expression):
    weather: PLAYER_WEATHERS

    def __init__(self, weather: PLAYER_WEATHERS) -> None:
        self.weather = weather

    def into_htsl(self) -> str:
        return f'playerWeather {self.inline_quoted(self.weather)}'

    def cloned(
        self,
        *,
        weather: PLAYER_WEATHERS | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'weather': weather,
            },
        )

    def equals(self, other: object) -> bool:
        if not isinstance(other, SetPlayerWeatherExpression):
            return False
        return self.weather == other.weather

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.weather}>'


def set_player_weather(weather: PLAYER_WEATHERS) -> None:
    SetPlayerWeatherExpression(weather=weather).write()
