from typing import TYPE_CHECKING, ClassVar, Literal, Self, cast, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.compiler.registry import ActionMeta
from pyhtsw.compiler.schedule import Effects, Resource, Stream
from pyhtsw.expression.expression import Expression
from pyhtsw.generated.enums import SOUND_NAME_TO_PATH, Sound
from pyhtsw.location import Location, ensure_location
from pyhtsw.utils.log import log

Weather = Literal['none', 'sunny', 'raining']

WEATHER_TO_HTSW: dict[Weather, str] = {
    'none': 'None',
    'sunny': 'Sunny',
    'raining': 'Raining',
}

_SOUND_PATHS = frozenset(Sound.__args__)  # type: ignore[attr-defined]


def resolve_sound(sound: 'Sound | str') -> 'Sound':
    if sound in _SOUND_PATHS:
        return cast('Sound', sound)
    mapped = SOUND_NAME_TO_PATH.get(sound)
    if mapped is not None:
        return mapped
    if '.' not in sound:
        raise ValueError(
            f'Unknown sound {sound!r}. Pass a sound id like "note.pling", or a '
            f'resource-pack sound key containing a dot.',
        )
    return cast('Sound', sound)


__all__ = (
    'PlaySoundExpression',
    'Weather',
    'play_sound',
    'resolve_sound',
    'PlayerTime',
    'SetPlayerTimeExpression',
    'set_player_time',
    'SetPlayerWeatherExpression',
    'set_player_weather',
)

if TYPE_CHECKING:
    from pyhtsw.execute.house import EmulatedHouse


@final
class PlaySoundExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='PLAY_SOUND',
        limit=25,
        effects=Effects.of(reads=(Resource.POSITION,), stream=Stream.SOUND),
        display_name='Play Sound',
        forbidden_events=('player_quit',),
    )

    sound: 'Sound'
    volume: float
    pitch: float
    location: Location
    check_valid: bool

    def __init__(
        self,
        sound: 'Sound | str',
        volume: float = 0.7,
        pitch: float = 1.0,
        location: Location | None = None,
        *,
        check_valid: bool = True,
    ) -> None:
        self.sound = resolve_sound(sound) if check_valid else cast('Sound', sound)
        self.volume = volume
        if check_valid and (self.volume < 0.0 or self.volume > 2.0):
            raise ValueError('volume must be between 0.0 and 2.0')
        self.pitch = pitch
        if check_valid and (self.pitch < 0.0 or self.pitch > 2.0):
            raise ValueError('pitch must be between 0.0 and 2.0')
        self.location = ensure_location(
            location if location is not None else Location.invokers(),
        )
        self.check_valid = check_valid

    def into_htsl(self) -> str:
        return (
            f'sound {self.inline_quoted(self.sound)} {self.inline(self.volume)}'
            f' {self.inline(self.pitch)} {self.location.into_htsl()}'
        )

    def raw_execute(self, context: 'EmulatedHouse') -> None:
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
        sound: 'Sound | str | Missing' = MISSING,
        volume: float | Missing = MISSING,
        pitch: float | Missing = MISSING,
        location: Location | None | Missing = MISSING,
        check_valid: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'sound': sound,
                'volume': volume,
                'pitch': pitch,
                'location': location,
                'check_valid': check_valid,
            },
        )


def play_sound(
    sound: 'Sound | str',
    volume: float = 0.7,
    pitch: float = 1.0,
    *,
    location: Location | None = None,
) -> None:
    PlaySoundExpression(
        sound=sound,
        volume=volume,
        pitch=pitch,
        location=location,
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
        forbidden_events=('player_quit',),
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
        forbidden_events=('player_quit',),
    )

    weather: Weather

    def __init__(self, weather: Weather) -> None:
        self.weather = weather

    def into_htsl(self) -> str:
        return f'playerWeather {self.inline_quoted(WEATHER_TO_HTSW[self.weather])}'

    def cloned(
        self,
        *,
        weather: Weather | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'weather': weather,
            },
        )


def set_player_weather(weather: Weather) -> None:
    SetPlayerWeatherExpression(weather=weather).write()
