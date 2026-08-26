from typing import TYPE_CHECKING, Self, cast, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.expression.expression import Expression
from pyhtsw.location import Location, resolve_location
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource, Stream
from pyhtsw.types import ALL_LOCATIONS, ALL_SOUNDS
from pyhtsw.utils.log import log

if TYPE_CHECKING:
    from pyhtsw.execute.context import ExecutionContext

__all__ = (
    'PlaySoundExpression',
    'custom_sound',
    'play_sound',
)


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
