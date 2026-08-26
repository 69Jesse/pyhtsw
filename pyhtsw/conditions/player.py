from typing import ClassVar, Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.compiler.registry import ConditionMeta
from pyhtsw.compiler.schedule import Resource
from pyhtsw.declarations.declared import declared_name
from pyhtsw.declarations.group import Group
from pyhtsw.declarations.region import Region
from pyhtsw.declarations.team import Team
from pyhtsw.expression.condition.condition import Condition
from pyhtsw.expression.condition.named_condition import NamedCondition
from pyhtsw.generated.enums import (
    PERMISSION_TO_HTSW,
    Gamemode,
    Permission,
    PotionEffect,
)

__all__ = (
    'IsFlyingCondition',
    'IsFlying',
    'IsSneakingCondition',
    'IsSneaking',
    'IsDoingParkourCondition',
    'IsDoingParkour',
    'CanPVPCondition',
    'CanPVP',
    'IsGamemode',
    'HasGroup',
    'HasTeam',
    'HasPermission',
    'WithinRegion',
    'HasPotionEffect',
)


class IsFlyingCondition(NamedCondition):
    htsw_meta = ConditionMeta(
        htsw_name='IS_FLYING',
        limit=20,
        reads=frozenset((Resource.GAMEMODE,)),
    )

    def __init__(self) -> None:
        super().__init__('isFlying')


IsFlying = IsFlyingCondition()


class IsSneakingCondition(NamedCondition):
    htsw_meta = ConditionMeta(
        htsw_name='IS_SNEAKING',
        limit=20,
        reads=frozenset(()),
    )

    def __init__(self) -> None:
        super().__init__('isSneaking')


IsSneaking = IsSneakingCondition()


class IsDoingParkourCondition(NamedCondition):
    htsw_meta = ConditionMeta(
        htsw_name='IS_DOING_PARKOUR',
        limit=1,
        reads=frozenset((Resource.PARKOUR,)),
    )

    def __init__(self) -> None:
        super().__init__('doingParkour')


IsDoingParkour = IsDoingParkourCondition()


class CanPVPCondition(NamedCondition):
    htsw_meta = ConditionMeta(
        htsw_name='PVP_ENABLED',
        limit=20,
        reads=frozenset(()),
        display_name='Can PvP',
        scoped_events=('pvp_state_change',),
    )

    def __init__(self) -> None:
        super().__init__('canPvp')


CanPVP = CanPVPCondition()


@final
class IsGamemode(Condition):
    htsw_meta = ConditionMeta(
        htsw_name='REQUIRE_GAMEMODE',
        limit=20,
        reads=frozenset((Resource.GAMEMODE,)),
    )

    gamemode: Gamemode

    def __init__(
        self,
        gamemode: Gamemode,
    ) -> None:
        self.gamemode = gamemode

    def into_htsl_raw(self) -> str:
        return f'gamemode {self.inline(self.gamemode)}'

    def cloned(
        self,
        *,
        gamemode: Gamemode | Missing = MISSING,
        inverted: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'gamemode': gamemode,
                'inverted': inverted,
            },
        )


@final
class HasGroup(Condition):
    htsw_meta = ConditionMeta(
        htsw_name='REQUIRE_GROUP',
        limit=20,
        reads=frozenset((Resource.GROUP,)),
    )

    group: str
    include_higher_groups: bool

    def __init__(
        self,
        group: 'Group | str',
        include_higher_groups: bool = False,
    ) -> None:
        self.group = declared_name(group)
        self.include_higher_groups = include_higher_groups

    def into_htsl_raw(self) -> str:
        return f'hasGroup {self.inline_quoted(self.group)} {self.inline(self.include_higher_groups)}'

    def cloned(
        self,
        *,
        group: 'Group | str | Missing' = MISSING,
        include_higher_groups: bool | Missing = MISSING,
        inverted: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'group': group,
                'include_higher_groups': include_higher_groups,
                'inverted': inverted,
            },
        )


@final
class HasTeam(Condition):
    htsw_meta = ConditionMeta(
        htsw_name='REQUIRE_TEAM',
        limit=20,
        reads=frozenset((Resource.TEAM,)),
    )

    team: str | None

    def __init__(
        self,
        team: 'Team | str | None',
    ) -> None:
        self.team = declared_name(team)

    def into_htsl_raw(self) -> str:
        return f'hasTeam {self.inline_quoted(self.team if self.team is not None else "None")}'

    def cloned(
        self,
        *,
        team: 'Team | str | None | Missing' = MISSING,
        inverted: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'team': team,
                'inverted': inverted,
            },
        )


@final
class HasPermission(Condition):
    htsw_meta = ConditionMeta(
        htsw_name='REQUIRE_PERMISSION',
        limit=20,
        reads=frozenset((Resource.GROUP,)),
    )

    permission: Permission

    def __init__(
        self,
        permission: Permission,
    ) -> None:
        self.permission = permission

    def into_htsl_raw(self) -> str:
        return (
            f'hasPermission {self.inline_quoted(PERMISSION_TO_HTSW[self.permission])}'
        )

    def cloned(
        self,
        *,
        permission: Permission | Missing = MISSING,
        inverted: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'permission': permission,
                'inverted': inverted,
            },
        )


def _region_name(region: 'Region | str') -> str:
    if isinstance(region, str):
        return region
    if isinstance(region, Region):
        return region.name
    raise TypeError(f'Expected a Region or str, got {region!r}')


@final
class WithinRegion(Condition):
    htsw_meta = ConditionMeta(
        htsw_name='IS_IN_REGION',
        limit=20,
        reads=frozenset((Resource.POSITION,)),
    )

    name: str
    __clone_map__: ClassVar[dict[str, str]] = {'region': 'name'}

    def __init__(self, region: 'Region | str') -> None:
        self.name = _region_name(region)

    def into_htsl_raw(self) -> str:
        return f'inRegion {self.inline_quoted(self.name)}'

    def cloned(
        self,
        *,
        region: 'Region | str | Missing' = MISSING,
        inverted: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'region': region,
                'inverted': inverted,
            },
        )


@final
class HasPotionEffect(Condition):
    htsw_meta = ConditionMeta(
        htsw_name='REQUIRE_POTION_EFFECT',
        limit=22,
        reads=frozenset((Resource.POTIONS,)),
    )

    effect: PotionEffect

    def __init__(
        self,
        effect: PotionEffect,
    ) -> None:
        self.effect = effect

    def into_htsl_raw(self) -> str:
        return f'hasPotion {self.inline_quoted(self.effect)}'

    def cloned(
        self,
        *,
        effect: PotionEffect | Missing = MISSING,
        inverted: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'effect': effect,
                'inverted': inverted,
            },
        )
