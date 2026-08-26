from typing import TYPE_CHECKING, ClassVar, Self, cast, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.compiler.registry import ActionMeta
from pyhtsw.compiler.schedule import Effects, Resource, Stream
from pyhtsw.expression.expression import Expression
from pyhtsw.location import Location, resolve_location
from pyhtsw.types import ALL_LOCATIONS, ALL_SOUNDS, PLAYER_WEATHERS
from pyhtsw.utils.log import log

__all__ = (
    'PlaySoundExpression',
    'custom_sound',
    'play_sound',
    'PlayerTime',
    'SetPlayerTimeExpression',
    'set_player_time',
    'SetPlayerWeatherExpression',
    'set_player_weather',
)

if TYPE_CHECKING:
    from pyhtsw.execute.context import ExecutionContext


def custom_sound(name: str) -> ALL_SOUNDS:
    return cast(ALL_SOUNDS, name)


@final
class PlaySoundExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='PLAY_SOUND',
        limit=25,
        effects=Effects.of(reads=(Resource.POSITION,), stream=Stream.SOUND),
        display_name='Play Sound',
        forbidden_events=('Player Quit',),
    )

    sound: ALL_SOUNDS
    volume: float
    pitch: float
    coordinates: str | None
    location: ALL_LOCATIONS
    check_valid: bool

    def __init__(
        self,
        sound: ALL_SOUNDS,
        volume: float = 0.7,
        pitch: float = 1.0,
        coordinates: str | None = None,
        location: ALL_LOCATIONS = 'invokers_location',
        *,
        check_valid: bool = True,
    ) -> None:
        self.sound = sound
        self.volume = volume
        if check_valid and (self.volume < 0.0 or self.volume > 2.0):
            raise ValueError('volume must be between 0.0 and 2.0')
        self.pitch = pitch
        if check_valid and (self.pitch < 0.0 or self.pitch > 2.0):
            raise ValueError('pitch must be between 0.0 and 2.0')
        self.coordinates = coordinates
        self.location = location
        self.check_valid = check_valid

    def into_htsl(self) -> str:
        line = f'sound {self.inline_quoted(self.sound)} {self.inline(self.volume)} {self.inline(self.pitch)} {self.inline_quoted(self.location)}'
        if self.location == 'custom_coordinates' and self.coordinates is not None:
            line += f' {self.inline_quoted(self.coordinates)}'
        return line

    def raw_execute(self, context: 'ExecutionContext') -> None:
        from pyhtsw.misc.sounds import preview_sound

        found = preview_sound(
            self.sound,
            volume=self.volume * context.volume_multiplier,
            pitch=self.pitch,
        )
        if not found:
            log(
                f'No sound found for \x1b[38;2;255;0;0m"{self.sound}"\x1b[0m, nothing will be played',
            )

    def cloned(
        self,
        *,
        sound: ALL_SOUNDS | Missing = MISSING,
        volume: float | Missing = MISSING,
        pitch: float | Missing = MISSING,
        coordinates: str | None | Missing = MISSING,
        location: ALL_LOCATIONS | Missing = MISSING,
        check_valid: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'sound': sound,
                'volume': volume,
                'pitch': pitch,
                'coordinates': coordinates,
                'location': location,
                'check_valid': check_valid,
            },
        )


def play_sound(
    sound: ALL_SOUNDS,
    volume: float = 0.7,
    pitch: float = 1.0,
    location: Location | None = None,
) -> None:
    keyword, coordinates = resolve_location(
        location if location is not None else Location.invokers(),
    )
    PlaySoundExpression(
        sound=sound,
        volume=volume,
        pitch=pitch,
        coordinates=coordinates,
        location=cast(ALL_LOCATIONS, keyword),
    ).write()


class PlayerTime:
    """The four presets Housing's selector offers. Any other tick value in
    [0, 24000) is accepted too."""

    SUNRISE: ClassVar[int] = 0
    NOON: ClassVar[int] = 6000
    SUNSET: ClassVar[int] = 12000
    MIDNIGHT: ClassVar[int] = 18000


@final
class SetPlayerTimeExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='SET_PLAYER_TIME',
        limit=5,
        effects=Effects.of(writes=(Resource.TIME,)),
        display_name='Set Player Time',
        forbidden_events=('Player Quit',),
    )

    time: int

    def __init__(self, time: int) -> None:
        self.time = time

    def into_htsl(self) -> str:
        return f'playerTime {self.inline(self.time)}'

    def cloned(
        self,
        *,
        time: int | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'time': time,
            },
        )


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


@final
class SetPlayerWeatherExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='SET_PLAYER_WEATHER',
        limit=5,
        effects=Effects.of(writes=(Resource.WEATHER,)),
        display_name='Set Player Weather',
        forbidden_events=('Player Quit',),
    )

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


def set_player_weather(weather: PLAYER_WEATHERS) -> None:
    SetPlayerWeatherExpression(weather=weather).write()
