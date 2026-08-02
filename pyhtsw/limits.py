from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .actions.function import Function
    from .expression.condition.condition import Condition
    from .expression.expression import Expression
    from .placeholders import PlaceholderEditable


# The action containers htsw distinguishes when resolving a limit.
ImportableKind = Literal[
    'functions',
    'events',
    'items',
    'menus',
    'regions',
    'commands',
    'npcs',
]
Nesting = Literal['conditional', 'random']

# A conditional in an *unnested* event container gets this instead of 25.
EVENT_CONDITIONAL_LIMIT = 25 + 15
# Measured in-game by htsw (2026-07): inside a Random action the server raises
# every per-type limit to at least this; higher limits keep their value.
RANDOM_FLOOR = 10

_LIMITS: dict[type['Expression'] | type['PlaceholderEditable'], int] | None = None
_CONDITION_LIMITS: dict[type['Condition'], int] | None = None


def get_limits() -> dict[type['Expression'] | type['PlaceholderEditable'], int]:
    global _LIMITS
    if _LIMITS is not None:
        return _LIMITS

    from .actions.apply_inventory_layout import ApplyInventoryLayoutExpression
    from .actions.apply_potion_effect import ApplyPotionEffectExpression
    from .actions.cancel_event import CancelEventExpression
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
    from .actions.exit_function import ExitFunctionExpression
    from .actions.fail_parkour import FailParkourExpression
    from .actions.full_heal import FullHealExpression
    from .actions.give_experience_levels import GiveExperienceLevelsExpression
    from .actions.give_item import GiveItemExpression
    from .actions.kill_player import KillPlayerExpression
    from .actions.launch_to_target import LaunchToTargetExpression
    from .actions.parkour_checkpoint import ParkourCheckpointExpression
    from .actions.pause_execution import PauseExecutionExpression
    from .actions.play_sound import PlaySoundExpression
    from .actions.player_health import PlayerHealthPlaceholder
    from .actions.player_hunger import PlayerHungerPlaceholder
    from .actions.player_max_health import PlayerMaxHealthPlaceholder
    from .actions.random import RandomExpression
    from .actions.remove_item import RemoveItemExpression
    from .actions.reset_inventory import ResetInventoryExpression
    from .actions.send_to_lobby import SendToLobbyExpression
    from .actions.set_compass_target import SetCompassTargetExpression
    from .actions.set_gamemode import SetGamemodeExpression
    from .actions.set_player_team import SetPlayerTeamExpression
    from .actions.set_player_time import SetPlayerTimeExpression
    from .actions.set_player_weather import SetPlayerWeatherExpression
    from .actions.teleport_player import TeleportPlayerExpression
    from .actions.toggle_nametag_display import ToggleNametagDisplayExpression
    from .actions.trigger_function import TriggerFunctionExpression
    from .expression.binary_expression import BinaryExpression
    from .expression.condition.conditional_expression import ConditionalExpression

    _LIMITS = {
        # expressions
        ConditionalExpression: 25,
        ChangePlayerGroupExpression: 1,
        KillPlayerExpression: 1,
        FullHealExpression: 5,
        DisplayTitleExpression: 5,
        DisplayActionBarExpression: 5,
        ResetInventoryExpression: 1,
        ParkourCheckpointExpression: 1,
        GiveItemExpression: 40,
        RemoveItemExpression: 40,
        ChatExpression: 20,
        ApplyPotionEffectExpression: 22,
        ClearPotionEffectsExpression: 5,
        GiveExperienceLevelsExpression: 5,
        BinaryExpression: 25,
        TeleportPlayerExpression: 5,
        FailParkourExpression: 1,
        PlaySoundExpression: 25,
        SetCompassTargetExpression: 5,
        SetGamemodeExpression: 1,
        RandomExpression: 25,
        TriggerFunctionExpression: 10,
        ApplyInventoryLayoutExpression: 5,
        EnchantHeldItemExpression: 24,
        PauseExecutionExpression: 30,
        SetPlayerTeamExpression: 1,
        DisplayMenuExpression: 10,
        DropItemExpression: 5,
        ChangeVelocityExpression: 5,
        LaunchToTargetExpression: 5,
        SetPlayerWeatherExpression: 5,
        SetPlayerTimeExpression: 5,
        ToggleNametagDisplayExpression: 5,
        ExitFunctionExpression: 1,
        CancelEventExpression: 1,
        CloseMenuExpression: 1,
        ConsumeItemExpression: 1,
        SendToLobbyExpression: 1,
        # placeholders
        PlayerMaxHealthPlaceholder: 5,
        PlayerHealthPlaceholder: 5,
        PlayerHungerPlaceholder: 5,
    }
    return _LIMITS


def get_condition_limits() -> dict[type['Condition'], int]:
    global _CONDITION_LIMITS
    if _CONDITION_LIMITS is not None:
        return _CONDITION_LIMITS

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
    from .actions.portal_type import PortalType
    from .actions.required_gamemode import RequiredGamemode
    from .actions.required_group import RequiredGroup
    from .actions.required_team import RequiredTeam
    from .actions.within_region import WithinRegion

    limits: dict[type[Condition], int] = {
        RequiredGroup: 20,
        HasPermission: 20,
        WithinRegion: 20,
        HasItem: 20,
        IsDoingParkourCondition: 1,
        DoingParkourCondition: 1,
        HasPotionEffect: 22,
        IsSneakingCondition: 20,
        IsFlyingCondition: 20,
        RequiredGamemode: 20,
        RequiredTeam: 20,
        DamageCause: 20,
        CanPVPCondition: 20,
        FishingEnvironment: 20,
        PortalType: 20,
        BlockType: 20,
        IsItem: 20,
        DamageAmountCondition: 20,
    }
    _CONDITION_LIMITS = limits
    return limits


# A ComparisonCondition maps to one of several htsw condition types depending on
# what it compares; each gets its own 20, so bucket them apart rather than
# lumping every comparison into one counter (which would be stricter than htsw).
COMPARISON_BUCKETS = ('COMPARE_HEALTH', 'COMPARE_MAX_HEALTH', 'COMPARE_HUNGER')
COMPARISON_LIMIT = 20

ConditionKey = type['Condition'] | str


def condition_into_key(condition: 'Condition') -> ConditionKey:
    from .actions.player_health import PlayerHealthPlaceholder
    from .actions.player_hunger import PlayerHungerPlaceholder
    from .actions.player_max_health import PlayerMaxHealthPlaceholder
    from .expression.condition.comparison_condition import ComparisonCondition
    from .stats.stat import Stat

    if not isinstance(condition, ComparisonCondition):
        return type(condition)
    left = condition.left
    if isinstance(left, PlayerHealthPlaceholder):
        return 'COMPARE_HEALTH'
    if isinstance(left, PlayerMaxHealthPlaceholder):
        return 'COMPARE_MAX_HEALTH'
    if isinstance(left, PlayerHungerPlaceholder):
        return 'COMPARE_HUNGER'
    if isinstance(left, Stat):
        return 'COMPARE_VAR'
    return 'COMPARE_PLACEHOLDER'


def get_condition_limit(key: ConditionKey) -> int | None:
    if isinstance(key, str):
        return COMPARISON_LIMIT
    return get_condition_limits().get(key)


def check_condition_limits(conditions: list['Condition'], *, where: str) -> None:
    """Raise if a condition list exceeds a per-type limit. Unlike actions this
    cannot be fixed by splitting — one Conditional owns one condition list — so
    it is an error rather than something to rewrite."""
    counts: dict[ConditionKey, int] = {}
    for condition in conditions:
        key = condition_into_key(condition)
        counts[key] = counts.get(key, 0) + 1
    for key, amount in counts.items():
        limit = get_condition_limit(key)
        if limit is not None and amount > limit:
            name = key if isinstance(key, str) else key.__name__
            raise RuntimeError(
                f'{where}: {amount} "{name}" conditions exceeds the limit of {limit}. '
                f'Split the check across nested conditionals or a triggered function.',
            )


def check_all_condition_limits(expressions: list['Expression']) -> None:
    """Walk a block's expressions (and their nested action lists) and validate
    every conditional's condition list."""
    from .expression.condition.conditional_expression import ConditionalExpression

    for expression in expressions:
        if isinstance(expression, ConditionalExpression):
            check_condition_limits(
                expression.conditions,
                where=f'Conditional {expression!r}',
            )
        for nested in expression.nested_expressions_refs():
            check_all_condition_limits(nested)


def get_limit(
    cls: type['Expression'] | type['PlaceholderEditable'],
    *,
    importable: ImportableKind = 'functions',
    nested: Nesting | None = None,
) -> int | None:
    from .expression.condition.conditional_expression import ConditionalExpression

    if cls is ConditionalExpression and importable == 'events' and nested is None:
        return EVENT_CONDITIONAL_LIMIT
    limit = get_limits().get(cls)
    if limit is not None and nested == 'random':
        return max(limit, RANDOM_FLOOR)
    return limit


ActionCounts = dict[type['Expression'] | type['PlaceholderEditable'], int]


class Counter:
    count: ActionCounts
    importable: ImportableKind
    nested: Nesting | None

    def __init__(
        self,
        memo: dict[int, ActionCounts] | None = None,
        *,
        importable: ImportableKind = 'functions',
        nested: Nesting | None = None,
    ) -> None:
        self.count = {}
        self.importable = importable
        self.nested = nested
        # Shared across the counters of one fix pass so the (somewhat costly)
        # flatten per expression happens at most once.
        self._memo = memo if memo is not None else {}

    def limit_for(
        self,
        cls: type['Expression'] | type['PlaceholderEditable'],
    ) -> int | None:
        return get_limit(cls, importable=self.importable, nested=self.nested)

    def nested_counter(self, nested: Nesting) -> 'Counter':
        return Counter(self._memo, importable=self.importable, nested=nested)

    @staticmethod
    def expression_into_cls(
        expression: 'Expression',
    ) -> type['Expression'] | type['PlaceholderEditable']:
        from .expression.binary_expression import BinaryExpression
        from .placeholders import PlaceholderEditable

        if isinstance(expression, BinaryExpression):
            expr = expression.into_assignment_expression()
            if isinstance(expr.left, PlaceholderEditable):
                return type(expr.left)
        return type(expression)

    def action_counts(self, expression: 'Expression') -> ActionCounts:
        """Rendered HTSL actions, by class, for one expression at its own block
        level. A `BinaryExpression` / `CompoundExpression` flattens into several
        actions (temps, modulo's if-block, ...), so counting the object as one
        undercounts the real actions and lets a block slip past its limit.

        Uses the flatten-only decomposition, not `into_executable_expressions()`:
        that method also runs the peephole optimizer and temp-stat renaming,
        which assume they see a whole block at once. Run on one expression in
        isolation (as every count here is), the optimizer can mistake a live
        store for a dead one, and renaming mutates not-yet-finalized temp-stat
        numbers as a side effect - so two different temp stats can end up
        compared as equal, undercounting a statement as a no-op it isn't (seen
        in practice: a `chunked()` chunk that measured under the limit still
        overflowed once the real, full-block finalize pass rendered it)."""
        from .expression.binary_expression import BinaryExpression
        from .expression.compound_expression import CompoundExpression

        key = id(expression)
        cached = self._memo.get(key)
        if cached is not None:
            return cached

        counts: ActionCounts = {}
        if isinstance(expression, BinaryExpression):
            rendered = expression.flatten()
        elif isinstance(expression, CompoundExpression):
            rendered = expression._flattened_expressions()  # noqa: SLF001
        else:
            rendered = (expression,)
        for rendered_expr in rendered:
            cls = self.expression_into_cls(rendered_expr)
            counts[cls] = counts.get(cls, 0) + 1
        self._memo[key] = counts
        return counts

    def increment(self, expression: 'Expression') -> None:
        for cls, amount in self.action_counts(expression).items():
            self.count[cls] = self.count.get(cls, 0) + amount

    def would_exceed(self, expression: 'Expression') -> bool:
        for cls, amount in self.action_counts(expression).items():
            limit = self.limit_for(cls)
            if limit is not None and self.count.get(cls, 0) + amount > limit:
                return True
        return False

    def exceeds_on_its_own(self, expression: 'Expression') -> bool:
        """A single expression that renders to more actions than the limit can
        never be made to fit by wrapping or moving it to a new block."""
        return Counter(
            self._memo,
            importable=self.importable,
            nested=self.nested,
        ).would_exceed(expression)


def nesting_of(expression: 'Expression') -> Nesting | None:
    """Which kind of container an expression's nested action lists live in."""
    from .actions.random import RandomExpression
    from .expression.condition.conditional_expression import ConditionalExpression

    if isinstance(expression, RandomExpression):
        return 'random'
    if isinstance(expression, ConditionalExpression):
        return 'conditional'
    return None


def is_within_limits(
    expressions: list['Expression'],
    *,
    importable: ImportableKind = 'functions',
    nested: Nesting | None = None,
) -> bool:
    counter = Counter(importable=importable, nested=nested)
    for expr in expressions:
        if counter.would_exceed(expr):
            return False
        counter.increment(expr)
    return True


def fix_action_limits(
    expressions: list['Expression'],
    *,
    nesting_possible: bool = True,
    function_if_exceeds: 'Function | None' = None,
    always_in_conditional: bool = False,
    importable: ImportableKind = 'functions',
) -> tuple[list['Expression'], list['Expression']]:
    """Fix action limits for a list of expressions.

    Returns a tuple of the fixed expressions that fit within a single block,
    and the remaining expressions that exceed the limits and need to be put in a new block.
    """
    from .actions.trigger_function import TriggerFunctionExpression
    from .expression.condition.conditional_expression import (
        ConditionalExpression,
        ConditionalMode,
    )

    check_all_condition_limits(expressions)

    result: list[Expression] = []
    memo: dict[int, ActionCounts] = {}
    global_counter = Counter(memo, importable=importable)
    index = 0

    while index < len(expressions):
        expr = expressions[index]
        can_nest = (nesting_possible or always_in_conditional) and expr.can_be_nested()
        should_wrap = can_nest and (
            always_in_conditional or global_counter.would_exceed(expr)
        )

        if can_nest and not should_wrap:
            if global_counter.would_exceed(expr):
                break
            global_counter.increment(expr)
            result.append(expr)
            index += 1
        elif should_wrap:
            # A lone expression rendering to more actions than fit in a block can
            # neither be wrapped nor moved; emit it as-is so we don't loop.
            if global_counter.exceeds_on_its_own(expr):
                global_counter.increment(expr)
                result.append(expr)
                index += 1
                continue

            dummy = ConditionalExpression([], ConditionalMode.ALL)
            if global_counter.would_exceed(dummy):
                break

            group: list[Expression] = []
            group_counter = Counter(memo, importable=importable, nested='conditional')
            while index < len(expressions) and expressions[index].can_be_nested():
                if group_counter.would_exceed(expressions[index]):
                    break
                group_counter.increment(expressions[index])
                group.append(expressions[index])
                index += 1

            if not group:
                break

            cond = ConditionalExpression(
                conditions=[],
                mode=ConditionalMode.ALL,
                if_expressions=group,
            )
            global_counter.increment(cond)
            result.append(cond)
        else:
            if global_counter.would_exceed(expr):
                break
            global_counter.increment(expr)
            result.append(expr)
            index += 1

    remaining = list(expressions[index:])

    if remaining and function_if_exceeds is not None:
        trigger = TriggerFunctionExpression(function_if_exceeds)
        placed = False

        if not global_counter.would_exceed(trigger):
            global_counter.increment(trigger)
            result.append(trigger)
            placed = True

        if not placed and nesting_possible:
            for j in range(len(result) - 1, -1, -1):
                candidate = result[j]
                if (
                    isinstance(candidate, ConditionalExpression)
                    and not candidate.conditions
                ):
                    inner_counter = Counter(
                        importable=importable,
                        nested='conditional',
                    )
                    for inner_expr in candidate.if_expressions:
                        inner_counter.increment(inner_expr)
                    if not inner_counter.would_exceed(trigger):
                        candidate.if_expressions.append(trigger)
                        placed = True
                    break

            if not placed:
                dummy = ConditionalExpression([], ConditionalMode.ALL)
                if not global_counter.would_exceed(dummy):
                    cond = ConditionalExpression(
                        conditions=[],
                        mode=ConditionalMode.ALL,
                        if_expressions=[trigger],
                    )
                    global_counter.increment(cond)
                    result.append(cond)
                    placed = True

        if not placed:
            while global_counter.would_exceed(trigger) and result:
                last = result.pop()
                global_counter = Counter(importable=importable)
                for r in result:
                    global_counter.increment(r)
                if isinstance(last, ConditionalExpression) and not last.conditions:
                    remaining = last.if_expressions + remaining
                else:
                    remaining = [last] + remaining

            global_counter.increment(trigger)
            result.append(trigger)

    for expr in result:
        nesting = nesting_of(expr)
        for nested_ref in expr.nested_expressions_refs():
            if not is_within_limits(
                nested_ref,
                importable=importable,
                nested=nesting,
            ):
                raise RuntimeError(
                    f'Expression {expr} contains nested expressions that exceed limits: {nested_ref}',
                )

    return result, remaining
