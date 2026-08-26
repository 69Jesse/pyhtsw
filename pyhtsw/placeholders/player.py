import re
from typing import final

import numpy as np

from pyhtsw.compiler.registry import ActionMeta
from pyhtsw.compiler.schedule import Effects, Resource
from pyhtsw.execute.backend_type import BackendType, JavaLong
from pyhtsw.internal_type import InternalType
from pyhtsw.placeholders.base import PlaceholderCheckable, PlaceholderEditable

__all__ = (
    'PlayerHealthPlaceholder',
    'PlayerHealth',
    'PlayerHungerPlaceholder',
    'PlayerHunger',
    'PlayerMaxHealthPlaceholder',
    'PlayerMaxHealth',
    'PlayerNamePlaceholder',
    'PlayerName',
    'PlayerPingPlaceholder',
    'PlayerPing',
    'PlayerVersionPlaceholder',
    'PlayerVersion',
    'PlayerProtocolPlaceholder',
    'PlayerProtocol',
    'PlayerExperiencePlaceholder',
    'PlayerExperience',
    'PlayerLevelPlaceholder',
    'PlayerLevel',
    'PlayerGamemodePlaceholder',
    'PlayerGamemode',
    'PlayerPositionXPlaceholder',
    'PlayerPositionX',
    'PlayerPositionYPlaceholder',
    'PlayerPositionY',
    'PlayerPositionZPlaceholder',
    'PlayerPositionZ',
    'PlayerPositionYawPlaceholder',
    'PlayerPositionYaw',
    'PlayerPositionPitchPlaceholder',
    'PlayerPositionPitch',
    'PlayerBlockXPlaceholder',
    'PlayerBlockX',
    'PlayerBlockYPlaceholder',
    'PlayerBlockY',
    'PlayerBlockZPlaceholder',
    'PlayerBlockZ',
)


@final
class PlayerHealthPlaceholder(
    PlaceholderEditable,
    pattern=re.compile(re.escape('%player.health%')),
    pattern_factory=lambda _: PlayerHealth,
):
    htsw_meta = ActionMeta(
        htsw_name='CHANGE_HEALTH',
        limit=5,
        effects=Effects.of(reads=(Resource.HEALTH,)),
        display_name='Change Health',
        forbidden_events=('Player Quit',),
    )

    def __init__(self) -> None:
        super().__init__(
            assignment_lhs='changeHealth',
            condition_lhs='health',
            placeholder='%player.health%',
            constant_internal_type=InternalType.DOUBLE,
        )

    def get_backend_value(self) -> BackendType:
        return np.float64(0)


PlayerHealth = PlayerHealthPlaceholder()


@final
class PlayerHungerPlaceholder(
    PlaceholderEditable,
    pattern=re.compile(re.escape('%player.hunger%')),
    pattern_factory=lambda _: PlayerHunger,
):
    htsw_meta = ActionMeta(
        htsw_name='CHANGE_HUNGER',
        limit=5,
        effects=Effects.of(reads=(Resource.HUNGER,)),
        display_name='Change Hunger Level',
        forbidden_events=('Player Quit',),
    )

    def __init__(self) -> None:
        super().__init__(
            assignment_lhs='hunger',
            placeholder='%player.hunger%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(0)


PlayerHunger = PlayerHungerPlaceholder()


@final
class PlayerMaxHealthPlaceholder(
    PlaceholderEditable,
    pattern=re.compile(re.escape('%player.maxhealth%')),
    pattern_factory=lambda _: PlayerMaxHealth,
):
    htsw_meta = ActionMeta(
        htsw_name='CHANGE_MAX_HEALTH',
        limit=5,
        effects=Effects.of(reads=(Resource.MAX_HEALTH,)),
        display_name='Change Max Health',
        forbidden_events=('Player Quit',),
    )

    def __init__(self) -> None:
        super().__init__(
            assignment_lhs='maxHealth',
            placeholder='%player.maxhealth%',
            constant_internal_type=InternalType.DOUBLE,
        )

    def get_backend_value(self) -> BackendType:
        return np.float64(0)


PlayerMaxHealth = PlayerMaxHealthPlaceholder()


@final
class PlayerNamePlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.name%')),
    pattern_factory=lambda _: PlayerName,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.name%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return 'Rfind'


PlayerName = PlayerNamePlaceholder()


@final
class PlayerPingPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.ping%')),
    pattern_factory=lambda _: PlayerPing,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.ping%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(0)


PlayerPing = PlayerPingPlaceholder()


@final
class PlayerVersionPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.version%')),
    pattern_factory=lambda _: PlayerVersion,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.version%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''


PlayerVersion = PlayerVersionPlaceholder()


@final
class PlayerProtocolPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.protocol%')),
    pattern_factory=lambda _: PlayerProtocol,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.protocol%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(0)


PlayerProtocol = PlayerProtocolPlaceholder()


@final
class PlayerExperiencePlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.experience%')),
    pattern_factory=lambda _: PlayerExperience,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.EXPERIENCE,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.experience%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(0)


PlayerExperience = PlayerExperiencePlaceholder()


@final
class PlayerLevelPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.level%')),
    pattern_factory=lambda _: PlayerLevel,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.EXPERIENCE,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.level%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(0)


PlayerLevel = PlayerLevelPlaceholder()


@final
class PlayerGamemodePlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.gamemode%')),
    pattern_factory=lambda _: PlayerGamemode,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.GAMEMODE,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.gamemode%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''


PlayerGamemode = PlayerGamemodePlaceholder()


@final
class PlayerPositionXPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.pos.x%')),
    pattern_factory=lambda _: PlayerPositionX,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.POSITION,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.pos.x%',
            constant_internal_type=InternalType.DOUBLE,
        )

    def get_backend_value(self) -> BackendType:
        return np.float64(0)


PlayerPositionX = PlayerPositionXPlaceholder()


@final
class PlayerPositionYPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.pos.y%')),
    pattern_factory=lambda _: PlayerPositionY,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.POSITION,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.pos.y%',
            constant_internal_type=InternalType.DOUBLE,
        )

    def get_backend_value(self) -> BackendType:
        return np.float64(0)


PlayerPositionY = PlayerPositionYPlaceholder()


@final
class PlayerPositionZPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.pos.z%')),
    pattern_factory=lambda _: PlayerPositionZ,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.POSITION,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.pos.z%',
            constant_internal_type=InternalType.DOUBLE,
        )

    def get_backend_value(self) -> BackendType:
        return np.float64(0)


PlayerPositionZ = PlayerPositionZPlaceholder()


@final
class PlayerPositionYawPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.pos.yaw%')),
    pattern_factory=lambda _: PlayerPositionYaw,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.POSITION,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.pos.yaw%',
            constant_internal_type=InternalType.DOUBLE,
        )

    def get_backend_value(self) -> BackendType:
        return np.float64(0)


PlayerPositionYaw = PlayerPositionYawPlaceholder()


@final
class PlayerPositionPitchPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.pos.pitch%')),
    pattern_factory=lambda _: PlayerPositionPitch,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.POSITION,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.pos.pitch%',
            constant_internal_type=InternalType.DOUBLE,
        )

    def get_backend_value(self) -> BackendType:
        return np.float64(0)


PlayerPositionPitch = PlayerPositionPitchPlaceholder()


@final
class PlayerBlockXPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.block.x%')),
    pattern_factory=lambda _: PlayerBlockX,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.POSITION,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.block.x%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(0)


PlayerBlockX = PlayerBlockXPlaceholder()


@final
class PlayerBlockYPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.block.y%')),
    pattern_factory=lambda _: PlayerBlockY,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.POSITION,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.block.y%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(0)


PlayerBlockY = PlayerBlockYPlaceholder()


@final
class PlayerBlockZPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.block.z%')),
    pattern_factory=lambda _: PlayerBlockZ,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(reads=(Resource.POSITION,)),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%player.block.z%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(0)


PlayerBlockZ = PlayerBlockZPlaceholder()
