from typing import Self, cast, final

from pyhtsw.checkable import Checkable
from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.compiler.registry import ActionMeta
from pyhtsw.compiler.schedule import Effects, Resource, Stream
from pyhtsw.declarations.group import Group
from pyhtsw.declarations.team import Team
from pyhtsw.expression.expression import Expression
from pyhtsw.expression.housing_type import NumericHousingType
from pyhtsw.location import Location, resolve_location
from pyhtsw.types import ALL_GAMEMODES, ALL_LOCATIONS, ALL_POTION_EFFECTS

__all__ = (
    'TeleportPlayerExpression',
    'teleport_player',
    'GoToHouseSpawnExpression',
    'go_to_house_spawn',
    'SetGamemodeExpression',
    'set_gamemode',
    'FullHealExpression',
    'full_heal',
    'KillPlayerExpression',
    'kill_player',
    'ApplyPotionEffectExpression',
    'apply_potion_effect',
    'ClearPotionEffectsExpression',
    'clear_potion_effects',
    'GiveExperienceLevelsExpression',
    'give_experience_levels',
    'ChangeVelocityExpression',
    'change_velocity',
    'LaunchToTargetExpression',
    'launch_to_target',
    'SetCompassTargetExpression',
    'set_compass_target',
    'ToggleNametagDisplayExpression',
    'toggle_nametag_display',
    'SetPlayerTeamExpression',
    'set_player_team',
    'ChangePlayerGroupExpression',
    'change_player_group',
    'ParkourCheckpointExpression',
    'parkour_checkpoint',
    'FailParkourExpression',
    'fail_parkour',
    'SendToLobbyExpression',
    'send_to_lobby',
)


@final
class TeleportPlayerExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='TELEPORT',
        limit=5,
        effects=Effects.of(reads=(Resource.POSITION,), writes=(Resource.POSITION,)),
        display_name='Teleport Player',
        forbidden_events=('Player Quit',),
    )

    coordinates: str | None
    location: ALL_LOCATIONS
    prevent_teleport_inside_block: bool

    def __init__(
        self,
        coordinates: str | None = None,
        location: ALL_LOCATIONS = 'custom_coordinates',
        prevent_teleport_inside_block: bool = False,
    ) -> None:
        self.coordinates = coordinates
        self.location = location
        self.prevent_teleport_inside_block = prevent_teleport_inside_block

    def into_htsl(self) -> str:
        line = f'tp {self.inline_quoted(self.location)}'
        if self.location == 'custom_coordinates' and self.coordinates is not None:
            line += f' {self.inline_quoted(self.coordinates)}'
        else:
            line += f' {self.inline_quoted("~ ~ ~")}'
        line += f' {self.inline(self.prevent_teleport_inside_block)}'
        return line

    def cloned(
        self,
        *,
        coordinates: str | None | Missing = MISSING,
        location: ALL_LOCATIONS | Missing = MISSING,
        prevent_teleport_inside_block: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'coordinates': coordinates,
                'location': location,
                'prevent_teleport_inside_block': prevent_teleport_inside_block,
            },
        )


def teleport_player(
    location: Location,
    prevent_teleport_inside_block: bool = False,
) -> None:
    keyword, coordinates = resolve_location(location)
    TeleportPlayerExpression(
        coordinates=coordinates,
        location=cast(ALL_LOCATIONS, keyword),
        prevent_teleport_inside_block=prevent_teleport_inside_block,
    ).write()


@final
class GoToHouseSpawnExpression(Expression):
    htsw_meta = ActionMeta(
        effects=Effects.of(writes=(Resource.POSITION,)),
    )

    def into_htsl(self) -> str:
        return 'houseSpawn'


def go_to_house_spawn() -> None:
    GoToHouseSpawnExpression().write()


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


@final
class FullHealExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='HEAL',
        limit=5,
        effects=Effects.of(
            writes=(
                Resource.HEALTH,
                Resource.HUNGER,
            ),
        ),
        display_name='Full Heal',
        forbidden_events=('Player Quit',),
    )

    def into_htsl(self) -> str:
        return 'fullHeal'


def full_heal() -> None:
    FullHealExpression().write()


@final
class KillPlayerExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='KILL',
        limit=1,
        effects=Effects.of(
            writes=(
                Resource.EXPERIENCE,
                Resource.HEALTH,
                Resource.HUNGER,
                Resource.INVENTORY,
                Resource.POSITION,
                Resource.POTIONS,
            ),
        ),
        display_name='Kill Player',
        forbidden_in_events=True,
    )

    def into_htsl(self) -> str:
        return 'kill'


def kill_player() -> None:
    KillPlayerExpression().write()


@final
class ApplyPotionEffectExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='APPLY_POTION_EFFECT',
        limit=22,
        effects=Effects.of(writes=(Resource.POTIONS,)),
        display_name='Apply Potion Effect',
        forbidden_events=('Player Quit',),
    )

    potion: ALL_POTION_EFFECTS
    duration: int
    level: int
    override_existing_effects: bool
    show_potion_icon: bool

    def __init__(
        self,
        potion: ALL_POTION_EFFECTS,
        duration: int = 60,
        level: int = 1,
        override_existing_effects: bool = False,
        show_potion_icon: bool = False,
    ) -> None:
        self.potion = potion
        self.duration = duration
        self.level = level
        self.override_existing_effects = override_existing_effects
        self.show_potion_icon = show_potion_icon

    def into_htsl(self) -> str:
        return (
            f'applyPotion {self.inline_quoted(self.potion)} {self.inline(self.duration)} {self.inline(self.level)}'
            f' {self.inline(self.override_existing_effects)} {self.inline(self.show_potion_icon)}'
        )

    def cloned(
        self,
        *,
        potion: ALL_POTION_EFFECTS | Missing = MISSING,
        duration: int | Missing = MISSING,
        level: int | Missing = MISSING,
        override_existing_effects: bool | Missing = MISSING,
        show_potion_icon: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'potion': potion,
                'duration': duration,
                'level': level,
                'override_existing_effects': override_existing_effects,
                'show_potion_icon': show_potion_icon,
            },
        )


def apply_potion_effect(
    potion: ALL_POTION_EFFECTS,
    duration: int = 60,
    level: int = 1,
    override_existing_effects: bool = False,
    show_potion_icon: bool = False,
) -> None:
    ApplyPotionEffectExpression(
        potion=potion,
        duration=duration,
        level=level,
        override_existing_effects=override_existing_effects,
        show_potion_icon=show_potion_icon,
    ).write()


@final
class ClearPotionEffectsExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='CLEAR_POTION_EFFECTS',
        limit=5,
        effects=Effects.of(writes=(Resource.POTIONS,)),
        display_name='Clear All Potion Effects',
        forbidden_events=('Player Quit',),
    )

    def into_htsl(self) -> str:
        return 'clearEffects'


def clear_potion_effects() -> None:
    ClearPotionEffectsExpression().write()


@final
class GiveExperienceLevelsExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='GIVE_EXPERIENCE_LEVELS',
        limit=5,
        effects=Effects.of(writes=(Resource.EXPERIENCE,)),
        display_name='Give Experience Levels',
        forbidden_events=('Player Quit',),
    )

    levels: int

    def __init__(self, levels: int) -> None:
        self.levels = levels

    def into_htsl(self) -> str:
        return f'xpLevel {self.inline(self.levels)}'

    def cloned(
        self,
        *,
        levels: int | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'levels': levels,
            },
        )


def give_experience_levels(levels: int) -> None:
    GiveExperienceLevelsExpression(levels=levels).write()


@final
class ChangeVelocityExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='SET_VELOCITY',
        limit=5,
        effects=Effects.of(writes=(Resource.VELOCITY,)),
        display_name='Change Velocity',
        forbidden_events=('Player Quit',),
    )

    x: Checkable | NumericHousingType
    y: Checkable | NumericHousingType
    z: Checkable | NumericHousingType

    def __init__(
        self,
        x: Checkable | NumericHousingType,
        y: Checkable | NumericHousingType,
        z: Checkable | NumericHousingType,
    ) -> None:
        self.x = x
        self.y = y
        self.z = z

    def into_htsl(self) -> str:
        return f'changeVelocity {self.inline(self.x)} {self.inline(self.y)} {self.inline(self.z)}'

    def cloned(
        self,
        *,
        x: Checkable | NumericHousingType | Missing = MISSING,
        y: Checkable | NumericHousingType | Missing = MISSING,
        z: Checkable | NumericHousingType | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'x': x,
                'y': y,
                'z': z,
            },
        )


def change_velocity(
    x: Checkable | NumericHousingType,
    y: Checkable | NumericHousingType,
    z: Checkable | NumericHousingType,
) -> None:
    ChangeVelocityExpression(x=x, y=y, z=z).write()


@final
class LaunchToTargetExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='LAUNCH',
        limit=5,
        effects=Effects.of(reads=(Resource.POSITION,), writes=(Resource.VELOCITY,)),
        display_name='Launch to Target',
        forbidden_events=('Player Quit',),
    )

    coordinates: str | None
    location: ALL_LOCATIONS
    strength: Checkable | int

    def __init__(
        self,
        coordinates: str | None = None,
        location: ALL_LOCATIONS = 'custom_coordinates',
        strength: Checkable | int = 2,
    ) -> None:
        self.coordinates = coordinates
        self.location = location
        self.strength = strength

    def into_htsl(self) -> str:
        line = f'launchTarget {self.inline_quoted(self.location)}'
        if self.location == 'custom_coordinates' and self.coordinates is not None:
            line += f' {self.inline_quoted(self.coordinates)}'
        else:
            line += f' {self.inline_quoted("~ ~ ~")}'
        line += f' {self.inline(self.strength)}'
        return line

    def cloned(
        self,
        *,
        coordinates: str | None | Missing = MISSING,
        location: ALL_LOCATIONS | Missing = MISSING,
        strength: Checkable | int | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'coordinates': coordinates,
                'location': location,
                'strength': strength,
            },
        )


def launch_to_target(
    location: Location,
    strength: Checkable | int = 2,
) -> None:
    keyword, coordinates = resolve_location(location)
    LaunchToTargetExpression(
        coordinates=coordinates,
        location=cast(ALL_LOCATIONS, keyword),
        strength=strength,
    ).write()


@final
class SetCompassTargetExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='SET_COMPASS_TARGET',
        limit=5,
        effects=Effects.of(writes=(Resource.COMPASS,)),
        display_name='Set Compass Target',
        forbidden_events=('Player Quit',),
    )

    coordinates: str | None
    location: ALL_LOCATIONS

    def __init__(
        self,
        coordinates: str | None = None,
        location: ALL_LOCATIONS = 'custom_coordinates',
    ) -> None:
        self.coordinates = coordinates
        self.location = location

    def into_htsl(self) -> str:
        line = f'compassTarget {self.inline_quoted(self.location)}'
        if self.location == 'custom_coordinates' and self.coordinates is not None:
            line += f' {self.inline_quoted(self.coordinates)}'
        return line

    def cloned(
        self,
        *,
        coordinates: str | None | Missing = MISSING,
        location: ALL_LOCATIONS | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'coordinates': coordinates,
                'location': location,
            },
        )


def set_compass_target(location: Location) -> None:
    keyword, coordinates = resolve_location(location)
    SetCompassTargetExpression(
        coordinates=coordinates,
        location=cast(ALL_LOCATIONS, keyword),
    ).write()


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


@final
class SetPlayerTeamExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='SET_TEAM',
        limit=1,
        effects=Effects.of(writes=(Resource.TEAM,)),
        display_name='Set Player Team',
        forbidden_events=('Player Quit',),
    )

    team: Team

    def __init__(self, team: Team) -> None:
        self.team = team

    def into_htsl(self) -> str:
        return f'setTeam {self.inline_quoted(self.team.name)}'

    def cloned(
        self,
        *,
        team: Team | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'team': team,
            },
        )


def set_player_team(team: Team | str) -> None:
    team = team if isinstance(team, Team) else Team(team)
    SetPlayerTeamExpression(team=team).write()


@final
class ChangePlayerGroupExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='SET_GROUP',
        limit=1,
        effects=Effects.of(writes=(Resource.GROUP,)),
        display_name="Change Player's Group",
        forbidden_events=(
            'Group Change',
            'Player Quit',
        ),
    )

    group: Group
    demotion_protection: bool

    def __init__(self, group: Group, demotion_protection: bool = True) -> None:
        self.group = group
        self.demotion_protection = demotion_protection

    def into_htsl(self) -> str:
        return f'changePlayerGroup {self.inline_quoted(self.group.name)} {self.inline(self.demotion_protection)}'

    def cloned(
        self,
        *,
        group: Group | Missing = MISSING,
        demotion_protection: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'group': group,
                'demotion_protection': demotion_protection,
            },
        )


def change_player_group(group: Group | str, demotion_protection: bool = True) -> None:
    group = group if isinstance(group, Group) else Group(group)
    ChangePlayerGroupExpression(
        group=group,
        demotion_protection=demotion_protection,
    ).write()


@final
class ParkourCheckpointExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='PARKOUR_CHECKPOINT',
        limit=1,
        effects=Effects.of(reads=(Resource.POSITION,), writes=(Resource.PARKOUR,)),
        display_name='Parkour Checkpoint',
        forbidden_events=('Player Quit',),
    )

    def into_htsl(self) -> str:
        return 'parkCheck'


def parkour_checkpoint() -> None:
    ParkourCheckpointExpression().write()


@final
class FailParkourExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='FAIL_PARKOUR',
        limit=1,
        effects=Effects.of(
            writes=(
                Resource.PARKOUR,
                Resource.POSITION,
            ),
            stream=Stream.TEXT,
        ),
        display_name='Fail Parkour',
        forbidden_events=('Player Quit',),
    )

    reason: str

    def __init__(self, reason: str = 'Failed!') -> None:
        self.reason = reason

    def into_htsl(self) -> str:
        return f'failParkour {self.inline_quoted(self.reason)}'

    def cloned(
        self,
        *,
        reason: str | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'reason': reason,
            },
        )


def fail_parkour(reason: str = 'Failed!') -> None:
    FailParkourExpression(reason=reason).write()


@final
class SendToLobbyExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='SEND_TO_LOBBY',
        limit=1,
        control=True,
        display_name='Send to Lobby',
        forbidden_in_events=True,
    )

    lobby: str

    def __init__(self, lobby: str) -> None:
        self.lobby = lobby

    def into_htsl(self) -> str:
        return f'lobby {self.inline_quoted(self.lobby)}'

    def cloned(
        self,
        *,
        lobby: str | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'lobby': lobby,
            },
        )


def send_to_lobby(lobby: str) -> None:
    SendToLobbyExpression(lobby=lobby).write()
