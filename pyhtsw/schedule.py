from bisect import insort
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .expression.condition.condition import Condition
    from .expression.expression import Expression
    from .limits import ImportableKind


__all__ = (
    'Effects',
    'Resource',
    'Stream',
    'build_dependencies',
    'effects_of',
    'reorder_for_folding',
    'reorder_for_packing',
)


class Resource(Enum):
    """A piece of mutable state two expressions can conflict over, besides the
    stats themselves. Only ever compared by identity, the values are for repr."""

    POSITION = 'position'
    VELOCITY = 'velocity'
    HEALTH = 'health'
    MAX_HEALTH = 'max_health'
    HUNGER = 'hunger'
    INVENTORY = 'inventory'
    POTIONS = 'potions'
    EXPERIENCE = 'experience'
    GAMEMODE = 'gamemode'
    TEAM = 'team'
    GROUP = 'group'
    COMPASS = 'compass'
    WEATHER = 'weather'
    TIME = 'time'
    NAMETAG = 'nametag'
    PARKOUR = 'parkour'
    MENU = 'menu'
    WORLD = 'world'
    # Read *and* written by every volatile placeholder (`%random.int%`, the unix
    # clock), which pins their relative order: swapping two reads of a value that
    # changes on every read swaps the values they produce.
    VOLATILE = 'volatile'


class Stream(Enum):
    """A channel the player perceives in order. Two expressions on the same
    stream never swap; expressions on different streams are free to, because
    within one tick the player receives them together."""

    TEXT = 'text'
    SOUND = 'sound'


type ResourceKey = Resource | tuple[object, ...]


@dataclass(frozen=True, slots=True)
class Effects:
    reads: frozenset[ResourceKey]
    writes: frozenset[ResourceKey]
    stream: Stream | None
    # Nothing may cross this expression in either direction.
    control: bool


BARRIER = Effects(frozenset(), frozenset(), None, True)


_ACTION_EFFECTS: dict[type, tuple[frozenset, frozenset, Stream | None]] | None = None
_CONTROL_TYPES: tuple[type, ...] | None = None
_PLACEHOLDER_RESOURCES: dict[type, tuple[frozenset, frozenset]] | None = None
_CONDITION_READS: dict[type, frozenset] | None = None


def _r(*resources: Resource) -> frozenset:
    return frozenset(resources)


def get_action_effects() -> dict[type, tuple[frozenset, frozenset, Stream | None]]:
    """(reads, writes, stream) per action type. Stats and placeholders named by
    an action's own fields are picked up generically on top of this table; what
    is declared here is the state an action touches *implicitly*."""
    global _ACTION_EFFECTS
    if _ACTION_EFFECTS is not None:
        return _ACTION_EFFECTS

    from .actions.apply_inventory_layout import ApplyInventoryLayoutExpression
    from .actions.apply_potion_effect import ApplyPotionEffectExpression
    from .actions.change_player_group import ChangePlayerGroupExpression
    from .actions.change_velocity import ChangeVelocityExpression
    from .actions.chat import ChatExpression
    from .actions.clear_potion_effects import ClearPotionEffectsExpression
    from .actions.close_menu import CloseMenuExpression
    from .actions.consume_item import ConsumeItemExpression
    from .actions.display_action_bar import DisplayActionBarExpression
    from .actions.display_menu import DisplayMenuExpression
    from .actions.display_title import DisplayTitleExpression
    from .actions.drop_item import DropItemExpression
    from .actions.enchant_held_item import EnchantHeldItemExpression
    from .actions.fail_parkour import FailParkourExpression
    from .actions.full_heal import FullHealExpression
    from .actions.give_experience_levels import GiveExperienceLevelsExpression
    from .actions.give_item import GiveItemExpression
    from .actions.go_to_house_spawn import GoToHouseSpawnExpression
    from .actions.kill_player import KillPlayerExpression
    from .actions.launch_to_target import LaunchToTargetExpression
    from .actions.parkour_checkpoint import ParkourCheckpointExpression
    from .actions.play_sound import PlaySoundExpression
    from .actions.random import RandomExpression
    from .actions.remove_item import RemoveItemExpression
    from .actions.reset_inventory import ResetInventoryExpression
    from .actions.set_compass_target import SetCompassTargetExpression
    from .actions.set_gamemode import SetGamemodeExpression
    from .actions.set_player_team import SetPlayerTeamExpression
    from .actions.set_player_time import SetPlayerTimeExpression
    from .actions.set_player_weather import SetPlayerWeatherExpression
    from .actions.teleport_player import TeleportPlayerExpression
    from .actions.toggle_nametag_display import ToggleNametagDisplayExpression

    empty = frozenset()
    _ACTION_EFFECTS = {
        ChatExpression: (empty, empty, Stream.TEXT),
        DisplayTitleExpression: (empty, empty, Stream.TEXT),
        DisplayActionBarExpression: (empty, empty, Stream.TEXT),
        # Announces the failure to the player and resets them to the start.
        FailParkourExpression: (
            empty,
            _r(Resource.PARKOUR, Resource.POSITION),
            Stream.TEXT,
        ),
        # Emitted at the player's feet, so it observes a teleport before it.
        PlaySoundExpression: (_r(Resource.POSITION), empty, Stream.SOUND),
        TeleportPlayerExpression: (_r(Resource.POSITION), _r(Resource.POSITION), None),
        GoToHouseSpawnExpression: (empty, _r(Resource.POSITION), None),
        ChangeVelocityExpression: (empty, _r(Resource.VELOCITY), None),
        LaunchToTargetExpression: (_r(Resource.POSITION), _r(Resource.VELOCITY), None),
        FullHealExpression: (empty, _r(Resource.HEALTH, Resource.HUNGER), None),
        KillPlayerExpression: (
            empty,
            _r(
                Resource.HEALTH,
                Resource.HUNGER,
                Resource.POSITION,
                Resource.INVENTORY,
                Resource.POTIONS,
                Resource.EXPERIENCE,
            ),
            None,
        ),
        ApplyPotionEffectExpression: (empty, _r(Resource.POTIONS), None),
        ClearPotionEffectsExpression: (empty, _r(Resource.POTIONS), None),
        GiveExperienceLevelsExpression: (empty, _r(Resource.EXPERIENCE), None),
        GiveItemExpression: (_r(Resource.INVENTORY), _r(Resource.INVENTORY), None),
        RemoveItemExpression: (_r(Resource.INVENTORY), _r(Resource.INVENTORY), None),
        ConsumeItemExpression: (_r(Resource.INVENTORY), _r(Resource.INVENTORY), None),
        EnchantHeldItemExpression: (
            _r(Resource.INVENTORY),
            _r(Resource.INVENTORY),
            None,
        ),
        ResetInventoryExpression: (empty, _r(Resource.INVENTORY), None),
        ApplyInventoryLayoutExpression: (empty, _r(Resource.INVENTORY), None),
        DropItemExpression: (
            _r(Resource.POSITION, Resource.INVENTORY),
            _r(Resource.WORLD, Resource.INVENTORY),
            None,
        ),
        SetCompassTargetExpression: (empty, _r(Resource.COMPASS), None),
        SetGamemodeExpression: (empty, _r(Resource.GAMEMODE), None),
        SetPlayerTeamExpression: (empty, _r(Resource.TEAM), None),
        ChangePlayerGroupExpression: (empty, _r(Resource.GROUP), None),
        SetPlayerTimeExpression: (empty, _r(Resource.TIME), None),
        SetPlayerWeatherExpression: (empty, _r(Resource.WEATHER), None),
        ToggleNametagDisplayExpression: (empty, _r(Resource.NAMETAG), None),
        ParkourCheckpointExpression: (
            _r(Resource.POSITION),
            _r(Resource.PARKOUR),
            None,
        ),
        DisplayMenuExpression: (empty, _r(Resource.MENU), None),
        CloseMenuExpression: (empty, _r(Resource.MENU), None),
        # Picking a branch consumes a random draw, so two of them keep their
        # order for the same reason two `%random.int%` reads do. Its branches are
        # summarised on top of this.
        RandomExpression: (_r(Resource.VOLATILE), _r(Resource.VOLATILE), None),
    }
    return _ACTION_EFFECTS


def get_control_types() -> tuple[type, ...]:
    """Types nothing may be moved across. Pauses split the tick (another
    player's function can run in between); the rest either leave the function or
    hand control to code this pass cannot see."""
    global _CONTROL_TYPES
    if _CONTROL_TYPES is not None:
        return _CONTROL_TYPES

    from .actions.cancel_event import CancelEventExpression
    from .actions.exit_function import ExitFunctionExpression
    from .actions.pause_execution import PauseExecutionExpression
    from .actions.send_to_lobby import SendToLobbyExpression
    from .actions.trigger_function import TriggerFunctionExpression
    from .execute.expressions.execution_expression import ExecutionExpression

    _CONTROL_TYPES = (
        PauseExecutionExpression,
        ExitFunctionExpression,
        CancelEventExpression,
        SendToLobbyExpression,
        TriggerFunctionExpression,
        ExecutionExpression,
    )
    return _CONTROL_TYPES


def get_placeholder_resources() -> dict[type, tuple[frozenset, frozenset]]:
    """(reads, writes) for every placeholder. A placeholder type missing from
    this table makes its expression a barrier, so a newly added one is safe by
    default rather than silently movable."""
    global _PLACEHOLDER_RESOURCES
    if _PLACEHOLDER_RESOURCES is not None:
        return _PLACEHOLDER_RESOURCES

    from .actions.date_unix import DateUnixMSPlaceholder, DateUnixPlaceholder
    from .actions.group_color import GroupColorPlaceholder
    from .actions.group_name import GroupNamePlaceholder
    from .actions.group_priority import GroupPriorityPlaceholder
    from .actions.group_tag import GroupTagPlaceholder
    from .actions.house_cookies import HouseCookiesPlaceholder
    from .actions.house_guests import HouseGuestsPlaceholder
    from .actions.house_players import HousePlayersPlaceholder
    from .actions.house_visiting_rules import HouseVisitingRulesPlaceholder
    from .actions.player_block_x import PlayerBlockXPlaceholder
    from .actions.player_block_y import PlayerBlockYPlaceholder
    from .actions.player_block_z import PlayerBlockZPlaceholder
    from .actions.player_experience import PlayerExperiencePlaceholder
    from .actions.player_gamemode import PlayerGamemodePlaceholder
    from .actions.player_health import PlayerHealthPlaceholder
    from .actions.player_hunger import PlayerHungerPlaceholder
    from .actions.player_level import PlayerLevelPlaceholder
    from .actions.player_max_health import PlayerMaxHealthPlaceholder
    from .actions.player_name import PlayerNamePlaceholder
    from .actions.player_ping import PlayerPingPlaceholder
    from .actions.player_position_pitch import PlayerPositionPitchPlaceholder
    from .actions.player_position_x import PlayerPositionXPlaceholder
    from .actions.player_position_y import PlayerPositionYPlaceholder
    from .actions.player_position_yaw import PlayerPositionYawPlaceholder
    from .actions.player_position_z import PlayerPositionZPlaceholder
    from .actions.player_protocol import PlayerProtocolPlaceholder
    from .actions.player_version import PlayerVersionPlaceholder
    from .actions.random_decimal import RandomDecimalPlaceholder
    from .actions.random_whole import RandomWholePlaceholder
    from .actions.server_name import ServerNamePlaceholder
    from .actions.server_short_name import ServerShortNamePlaceholder
    from .actions.team_color import TeamColorPlaceholder
    from .actions.team_name import TeamNamePlaceholder
    from .actions.team_players import TeamPlayersPlaceholder
    from .actions.team_tag import TeamTagPlaceholder

    empty = frozenset()

    def read(resource: Resource) -> tuple[frozenset, frozenset]:
        return (_r(resource), empty)

    def volatile() -> tuple[frozenset, frozenset]:
        return (_r(Resource.VOLATILE), _r(Resource.VOLATILE))

    def pure() -> tuple[frozenset, frozenset]:
        return (empty, empty)

    _PLACEHOLDER_RESOURCES = {
        PlayerHealthPlaceholder: read(Resource.HEALTH),
        PlayerMaxHealthPlaceholder: read(Resource.MAX_HEALTH),
        PlayerHungerPlaceholder: read(Resource.HUNGER),
        PlayerPositionXPlaceholder: read(Resource.POSITION),
        PlayerPositionYPlaceholder: read(Resource.POSITION),
        PlayerPositionZPlaceholder: read(Resource.POSITION),
        PlayerPositionYawPlaceholder: read(Resource.POSITION),
        PlayerPositionPitchPlaceholder: read(Resource.POSITION),
        PlayerBlockXPlaceholder: read(Resource.POSITION),
        PlayerBlockYPlaceholder: read(Resource.POSITION),
        PlayerBlockZPlaceholder: read(Resource.POSITION),
        PlayerExperiencePlaceholder: read(Resource.EXPERIENCE),
        PlayerLevelPlaceholder: read(Resource.EXPERIENCE),
        PlayerGamemodePlaceholder: read(Resource.GAMEMODE),
        GroupNamePlaceholder: read(Resource.GROUP),
        GroupColorPlaceholder: read(Resource.GROUP),
        GroupTagPlaceholder: read(Resource.GROUP),
        GroupPriorityPlaceholder: read(Resource.GROUP),
        TeamNamePlaceholder: read(Resource.TEAM),
        TeamColorPlaceholder: read(Resource.TEAM),
        TeamTagPlaceholder: read(Resource.TEAM),
        TeamPlayersPlaceholder: read(Resource.TEAM),
        RandomWholePlaceholder: volatile(),
        RandomDecimalPlaceholder: volatile(),
        DateUnixPlaceholder: volatile(),
        DateUnixMSPlaceholder: volatile(),
        # Constant for the duration of a tick, and nothing here writes them.
        PlayerNamePlaceholder: pure(),
        PlayerPingPlaceholder: pure(),
        PlayerVersionPlaceholder: pure(),
        PlayerProtocolPlaceholder: pure(),
        ServerNamePlaceholder: pure(),
        ServerShortNamePlaceholder: pure(),
        HouseCookiesPlaceholder: pure(),
        HouseGuestsPlaceholder: pure(),
        HousePlayersPlaceholder: pure(),
        HouseVisitingRulesPlaceholder: pure(),
    }
    return _PLACEHOLDER_RESOURCES


def get_condition_reads() -> dict[type, frozenset]:
    """What each condition type inspects beyond the stats it names. A condition
    type missing from this table makes its whole conditional a barrier."""
    global _CONDITION_READS
    if _CONDITION_READS is not None:
        return _CONDITION_READS

    from .actions.block_type import BlockType
    from .actions.can_pvp import CanPVPCondition
    from .actions.damage_amount import DamageAmountCondition
    from .actions.damage_cause import DamageCause
    from .actions.doing_parkour import DoingParkourCondition
    from .actions.fishing_environment import FishingEnvironment
    from .actions.has_item import HasItem
    from .actions.has_permission import HasPermission
    from .actions.has_potion_effect import HasPotionEffect
    from .actions.is_doing_parkour import IsDoingParkourCondition
    from .actions.is_flying import IsFlyingCondition
    from .actions.is_item import IsItem
    from .actions.is_sneaking import IsSneakingCondition
    from .actions.player_flying import PlayerFlyingCondition
    from .actions.player_sneaking import PlayerSneakingCondition
    from .actions.portal_type import PortalType
    from .actions.required_gamemode import RequiredGamemode
    from .actions.required_group import RequiredGroup
    from .actions.required_team import RequiredTeam
    from .actions.within_region import WithinRegion
    from .expression.condition.comparison_condition import ComparisonCondition

    empty = frozenset()
    _CONDITION_READS = {
        ComparisonCondition: empty,  # its operands are picked up generically
        WithinRegion: _r(Resource.POSITION),
        HasItem: _r(Resource.INVENTORY),
        IsItem: _r(Resource.INVENTORY),
        HasPotionEffect: _r(Resource.POTIONS),
        HasPermission: _r(Resource.GROUP),
        RequiredGroup: _r(Resource.GROUP),
        RequiredTeam: _r(Resource.TEAM),
        RequiredGamemode: _r(Resource.GAMEMODE),
        IsFlyingCondition: _r(Resource.GAMEMODE),
        PlayerFlyingCondition: _r(Resource.GAMEMODE),
        DoingParkourCondition: _r(Resource.PARKOUR),
        IsDoingParkourCondition: _r(Resource.PARKOUR),
        IsSneakingCondition: empty,
        PlayerSneakingCondition: empty,
        CanPVPCondition: empty,
        DamageCause: empty,
        DamageAmountCondition: empty,
        FishingEnvironment: empty,
        PortalType: empty,
        BlockType: empty,
    }
    return _CONDITION_READS


class _Collector:
    __slots__ = ('ok', 'reads', 'writes')

    def __init__(self) -> None:
        self.reads: set[ResourceKey] = set()
        self.writes: set[ResourceKey] = set()
        self.ok = True

    def checkable(self, value: object, *, write: bool = False) -> None:
        from .checkable import Checkable
        from .expression.binary_expression import BinaryExpression
        from .expression.compound_expression import CompoundExpression
        from .placeholders import PlaceholderCheckable
        from .stats.stat import Stat

        if isinstance(value, CompoundExpression):
            # A compound really does run its inner statements (`abs()` and `%`
            # expand into one), so its writes are writes.
            inner = effects_of(value)
            if inner.control:
                self.ok = False
                return
            self.reads.update(inner.reads)
            self.writes.update(inner.writes)
            return
        if isinstance(value, BinaryExpression):
            # An operand tree: everything inside it is read, including the
            # inner `left`s, which are operands rather than assignment targets.
            for expr in value.walk_expressions():
                if isinstance(expr, CompoundExpression):
                    self.checkable(expr)
                    continue
                self.expression_fields(expr, treat_all_as_reads=True)
            return
        if isinstance(value, Stat):
            key = value.into_hashable()
            (self.writes if write else self.reads).add(key)
            return
        if isinstance(value, PlaceholderCheckable):
            entry = get_placeholder_resources().get(type(value))
            if entry is None:
                self.ok = False
                return
            reads, writes = entry
            self.reads.update(reads)
            self.writes.update(writes)
            if write:
                self.writes.update(reads)
            return
        if isinstance(value, Checkable):
            self.ok = False

    def text(self, value: str) -> None:
        from .checkable import Checkable

        for ref in Checkable.iter_in_string(value):
            self.checkable(ref)

    def expression_fields(
        self,
        expression: 'Expression',
        *,
        treat_all_as_reads: bool = False,
    ) -> None:
        from .expression.binary_expression import BinaryExpression, BinaryOperator

        is_assignment = (
            not treat_all_as_reads
            and isinstance(expression, BinaryExpression)
            and expression.is_assignment_expression()
        )
        for key, value in expression._get_all_values().items():  # noqa: SLF001
            if is_assignment and key == 'left':
                self.checkable(value, write=True)
                # Everything except a plain `=` reads the target first.
                if expression.operator is not BinaryOperator.Set:  # type: ignore[attr-defined]
                    self.checkable(value)
                continue
            if isinstance(value, str):
                self.text(value)
                continue
            self.checkable(value)

    def condition(self, condition: 'Condition') -> None:
        reads = get_condition_reads().get(type(condition))
        if reads is None:
            self.ok = False
            return
        self.reads.update(reads)
        for value in vars(condition).values():
            if isinstance(value, str):
                self.text(value)
            else:
                self.checkable(value)


def effects_of(expression: 'Expression') -> Effects:
    """What `expression` reads, writes and displays. Anything this pass does not
    recognise comes back as a barrier, so an unclassified action can only ever
    cost packing, never correctness."""
    from .expression.binary_expression import BinaryExpression
    from .expression.compound_expression import CompoundExpression
    from .expression.condition.conditional_expression import ConditionalExpression
    from .expression.unset_expression import UnsetExpression

    if isinstance(expression, get_control_types()):
        return BARRIER

    collector = _Collector()
    stream: Stream | None = None

    if isinstance(expression, BinaryExpression):
        collector.expression_fields(expression)
    elif isinstance(expression, UnsetExpression):
        collector.checkable(expression.target, write=True)
    elif isinstance(expression, CompoundExpression):
        for inner in expression.expressions:
            inner_effects = effects_of(inner)
            if inner_effects.control:
                return BARRIER
            collector.reads.update(inner_effects.reads)
            collector.writes.update(inner_effects.writes)
            stream = stream or inner_effects.stream
        collector.checkable(expression.result)
    elif isinstance(expression, ConditionalExpression):
        for condition in expression.conditions:
            collector.condition(condition)
        summary = _summarize_bodies(expression)
        if summary is None:
            return BARRIER
        reads, writes, stream = summary
        collector.reads.update(reads)
        collector.writes.update(writes)
    else:
        entry = get_action_effects().get(type(expression))
        nested = expression.nested_expressions_refs()
        if entry is None and not nested:
            return BARRIER
        if entry is not None:
            reads, writes, stream = entry
            collector.reads.update(reads)
            collector.writes.update(writes)
            collector.expression_fields(expression, treat_all_as_reads=True)
        if nested:
            summary = _summarize_bodies(expression)
            if summary is None:
                return BARRIER
            reads, writes, body_stream = summary
            collector.reads.update(reads)
            collector.writes.update(writes)
            stream = stream or body_stream
            if entry is None:
                collector.expression_fields(expression, treat_all_as_reads=True)

    if not collector.ok:
        return BARRIER
    return Effects(
        frozenset(collector.reads),
        frozenset(collector.writes),
        stream,
        False,
    )


def conditions_read(conditions: list['Condition']) -> frozenset | None:
    """Everything a condition list inspects, or `None` if any of it is a
    condition type this pass does not know."""
    collector = _Collector()
    for condition in conditions:
        collector.condition(condition)
    if not collector.ok:
        return None
    return frozenset(collector.reads)


def body_writes(expression: 'Expression') -> frozenset | None:
    """Everything an expression's nested action lists write, or `None` if any of
    them is a barrier."""
    summary = _summarize_bodies(expression)
    if summary is None:
        return None
    return summary[1]


def _summarize_bodies(
    expression: 'Expression',
) -> tuple[frozenset, frozenset, Stream | None] | None:
    reads: set[ResourceKey] = set()
    writes: set[ResourceKey] = set()
    stream: Stream | None = None
    for body in expression.nested_expressions_refs():
        for inner in body:
            inner_effects = effects_of(inner)
            if inner_effects.control:
                return None
            reads.update(inner_effects.reads)
            writes.update(inner_effects.writes)
            stream = stream or inner_effects.stream
    return frozenset(reads), frozenset(writes), stream


def _ordering_barrier(expression: 'Expression', effects: Effects) -> bool:
    from .actions.strict_order import strict_order_region_of

    return effects.control or strict_order_region_of(expression) is not None


def build_dependencies(expressions: list['Expression']) -> list[set[int]]:
    """Predecessor sets: `i in preds[j]` means `i` must still run before `j`.
    Any topological order of this graph emits the same house."""
    effects = [effects_of(expression) for expression in expressions]
    preds: list[set[int]] = [set() for _ in expressions]

    last_writer: dict[ResourceKey, int] = {}
    readers_since_write: dict[ResourceKey, list[int]] = {}
    last_on_stream: dict[Stream, int] = {}
    last_barrier: int | None = None
    since_barrier: list[int] = []

    for index, current in enumerate(effects):
        if last_barrier is not None:
            preds[index].add(last_barrier)

        if _ordering_barrier(expressions[index], current):
            # Everything since the previous barrier must precede this one; the
            # edge above then carries the rest transitively.
            preds[index].update(since_barrier)
            last_barrier = index
            since_barrier = []
        else:
            since_barrier.append(index)

        for resource in current.reads:
            writer = last_writer.get(resource)
            if writer is not None:
                preds[index].add(writer)
            readers_since_write.setdefault(resource, []).append(index)

        for resource in current.writes:
            writer = last_writer.get(resource)
            if writer is not None:
                preds[index].add(writer)
            for reader in readers_since_write.get(resource, ()):
                if reader != index:
                    preds[index].add(reader)
            readers_since_write[resource] = []
            last_writer[resource] = index

        if current.stream is not None:
            previous = last_on_stream.get(current.stream)
            if previous is not None:
                preds[index].add(previous)
            last_on_stream[current.stream] = index

    return preds


def is_legal_order(order: list[int], preds: list[set[int]]) -> bool:
    seen: set[int] = set()
    for index in order:
        if not preds[index] <= seen:
            return False
        seen.add(index)
    return True


def _list_schedule(
    preds: list[set[int]],
    prefer: Callable[[list[int], list[int]], int],
) -> list[int]:
    total = len(preds)
    remaining = [len(pred) for pred in preds]
    successors: list[list[int]] = [[] for _ in range(total)]
    for index, pred_set in enumerate(preds):
        for pred in pred_set:
            successors[pred].append(index)

    ready = [index for index in range(total) if remaining[index] == 0]
    ready.sort()
    order: list[int] = []
    while ready:
        chosen = prefer(ready, order)
        ready.remove(chosen)
        order.append(chosen)
        for successor in successors[chosen]:
            remaining[successor] -= 1
            if remaining[successor] == 0:
                # Kept sorted so ties always fall back to the original order.
                insort(ready, successor)
    return order


def _written_stat_key(expression: 'Expression') -> object | None:
    from .expression.binary_expression import BinaryExpression
    from .stats.stat import Stat

    if isinstance(expression, BinaryExpression) and isinstance(expression.left, Stat):
        return expression.left.into_hashable()
    return None


def reorder_for_folding(expressions: list['Expression']) -> list['Expression'] | None:
    """Cluster consecutive writes to the same stat together so the constant-fold
    and dead-store passes, which only look at neighbours, can fire. Returns the
    new order, or `None` when nothing moved."""
    if len(expressions) < 2:
        return None
    preds = build_dependencies(expressions)
    keys = [_written_stat_key(expression) for expression in expressions]

    def prefer(ready: list[int], order: list[int]) -> int:
        if order:
            last_key = keys[order[-1]]
            if last_key is not None:
                for candidate in ready:
                    if keys[candidate] == last_key:
                        return candidate
        return ready[0]

    order = _list_schedule(preds, prefer)
    if order == list(range(len(expressions))):
        return None
    return [expressions[index] for index in order]


def _is_nestable(expression: 'Expression') -> bool:
    return expression.can_be_nested()


def _packing_cost(
    expressions: list['Expression'],
    importable: 'ImportableKind',
    memo: dict,
) -> tuple[int, int]:
    from .limits import packing_cost

    return packing_cost(expressions, importable=importable, memo=memo)


def _greedy_pack_order(preds: list[set[int]], nestable: list[bool]) -> list[int]:

    def prefer(ready: list[int], order: list[int]) -> int:
        want = nestable[order[-1]] if order else True
        for candidate in ready:
            if nestable[candidate] == want:
                return candidate
        return ready[0]

    return _list_schedule(preds, prefer)


def _exact_pack_order(
    expressions: list['Expression'],
    preds: list[set[int]],
    importable: 'ImportableKind',
    incumbent: list[int],
    incumbent_cost: tuple[int, int],
    memo: dict,
) -> tuple[list[int], tuple[int, int]]:
    total = len(expressions)
    best_order = incumbent
    best_cost = incumbent_cost
    seen: set[frozenset[int]] = set()
    budget = EXACT_NODE_BUDGET

    def search(order: list[int], emitted: frozenset[int]) -> None:
        nonlocal best_order, best_cost, budget
        if budget <= 0:
            return
        budget -= 1
        if len(order) == total:
            cost = _packing_cost(
                [expressions[index] for index in order],
                importable,
                memo,
            )
            if cost < best_cost:
                best_cost = cost
                best_order = list(order)
            return
        if emitted in seen:
            return
        seen.add(emitted)
        for candidate in range(total):
            if candidate in emitted or not preds[candidate] <= emitted:
                continue
            order.append(candidate)
            search(order, emitted | {candidate})
            order.pop()

    search([], frozenset())
    return best_order, best_cost


# Above this many expressions the exhaustive search is hopeless - the number of
# legal orders is exponential in the width of the dependency graph.
EXACT_SEARCH_LIMIT = 12
EXACT_NODE_BUDGET = 20_000
# Local search costs a full replan per candidate move, so it is worth it only
# while the block is small enough for the quadratic move set to stay cheap. The
# greedy schedule already minimises the number of nestable/non-nestable
# alternations, which is the term that decides the wrapper count; local search
# only recovers the cases where a wrapper's capacity, not the order, was binding.
LOCAL_SEARCH_LIMIT = 64
LOCAL_SEARCH_BUDGET = 400


def _local_improve(
    expressions: list['Expression'],
    preds: list[set[int]],
    order: list[int],
    cost: tuple[int, int],
    importable: 'ImportableKind',
    memo: dict,
) -> tuple[list[int], tuple[int, int]]:
    budget = LOCAL_SEARCH_BUDGET
    improved = True
    while improved and budget > 0:
        improved = False
        for position in range(len(order)):
            for target in range(len(order)):
                if target == position or budget <= 0:
                    continue
                budget -= 1
                candidate = list(order)
                node = candidate.pop(position)
                candidate.insert(target, node)
                if not is_legal_order(candidate, preds):
                    continue
                candidate_cost = _packing_cost(
                    [expressions[index] for index in candidate],
                    importable,
                    memo,
                )
                if candidate_cost < cost:
                    order = candidate
                    cost = candidate_cost
                    improved = True
                    break
            if improved:
                break
    return order, cost


def reorder_for_packing(
    expressions: list['Expression'],
    *,
    importable: 'ImportableKind' = 'functions',
) -> list['Expression'] | None:
    """Reorder a block so the limit fixer needs as few wrapper conditionals and
    overflow functions as possible. Returns `None` when the source order is
    already as good as anything reachable."""
    if len(expressions) < 2:
        return None

    # One memo for every candidate order: the action counts are keyed by
    # expression identity, so the flatten behind them survives reordering.
    memo: dict = {}
    base_cost = _packing_cost(expressions, importable, memo)
    if base_cost == (0, 0):
        return None

    preds = build_dependencies(expressions)
    nestable = [_is_nestable(expression) for expression in expressions]
    identity = list(range(len(expressions)))

    order = _greedy_pack_order(preds, nestable)
    cost = _packing_cost([expressions[index] for index in order], importable, memo)
    if cost > base_cost:
        order, cost = identity, base_cost

    if len(expressions) <= LOCAL_SEARCH_LIMIT:
        order, cost = _local_improve(
            expressions,
            preds,
            order,
            cost,
            importable,
            memo,
        )

    if len(expressions) <= EXACT_SEARCH_LIMIT:
        order, cost = _exact_pack_order(
            expressions,
            preds,
            importable,
            order,
            cost,
            memo,
        )

    if cost >= base_cost or order == identity:
        return None
    return [expressions[index] for index in order]
