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

# Only a function may absorb the tail an action list could not hold. Triggering
# a function costs 4 ticks, and a click handler can fire faster than that, so
# carving one out of an item/menu/npc/region/event/command block would silently
# drop or reorder the tail. Those raise `ActionLimitError` instead.
FUNCTION_OVERFLOW_KINDS: frozenset[ImportableKind] = frozenset({'functions'})


class ActionLimitError(RuntimeError):
    """An action list is over a Housing limit and cannot be fixed automatically.

    Subclasses `RuntimeError` so existing handlers keep catching it."""


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

    from .registry import iter_action_types, iter_placeholder_types

    limits: dict[type[Expression] | type[PlaceholderEditable], int] = {}
    for cls in (*iter_action_types(), *iter_placeholder_types()):
        meta = cls.__dict__.get('htsw_meta')
        if meta is not None and meta.limit is not None:
            limits[cls] = meta.limit
    _LIMITS = limits
    return _LIMITS


def get_condition_limits() -> dict[type['Condition'], int]:
    global _CONDITION_LIMITS
    if _CONDITION_LIMITS is not None:
        return _CONDITION_LIMITS

    from .registry import iter_condition_types

    limits: dict[type[Condition], int] = {}
    for cls in iter_condition_types():
        meta = cls.__dict__.get('htsw_meta')
        if meta is not None and meta.limit is not None:
            limits[cls] = meta.limit
    _CONDITION_LIMITS = limits
    return _CONDITION_LIMITS


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


def total_action_count(expressions: list['Expression']) -> int:
    """Every HTSL action these expressions render to, nested action lists
    included. The measure the fold-enabling reorder has to beat before its order
    is adopted."""
    counter = Counter()
    total = 0
    for expression in expressions:
        total += sum(counter.action_counts(expression).values())
        for nested in expression.nested_expressions_refs():
            total += total_action_count(nested)
    return total


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


type PlanItem = tuple[str, list['Expression']]


def plan_packing(
    expressions: list['Expression'],
    *,
    nesting_possible: bool = True,
    always_in_conditional: bool = False,
    importable: ImportableKind = 'functions',
    memo: dict[int, ActionCounts] | None = None,
) -> tuple[list[PlanItem], int, 'Counter']:
    """Decide how a block's expressions pack into the container without building
    anything: a list of `('direct', [expr])` / `('wrap', [exprs...])` items, the
    index where the block ran out of room, and the counter holding the resulting
    action counts. `fix_action_limits` builds the objects from this, and the
    scheduler costs candidate orders with it."""
    from .expression.condition.conditional_expression import (
        ConditionalExpression,
        ConditionalMode,
    )

    if memo is None:
        memo = {}
    items: list[PlanItem] = []
    global_counter = Counter(memo, importable=importable)
    index = 0
    # Counting a wrapper never inspects its body, so one instance serves for
    # every wrapper this plan measures.
    dummy = ConditionalExpression([], ConditionalMode.ALL)

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
            items.append(('direct', [expr]))
            index += 1
        elif should_wrap:
            # A lone expression rendering to more actions than fit in a block can
            # neither be wrapped nor moved; emit it as-is so we don't loop.
            if global_counter.exceeds_on_its_own(expr):
                global_counter.increment(expr)
                items.append(('direct', [expr]))
                index += 1
                continue

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

            global_counter.increment(dummy)
            items.append(('wrap', group))
        else:
            if global_counter.would_exceed(expr):
                break
            global_counter.increment(expr)
            items.append(('direct', [expr]))
            index += 1

    return items, index, global_counter


def packing_cost(
    expressions: list['Expression'],
    *,
    importable: ImportableKind = 'functions',
    memo: dict[int, ActionCounts] | None = None,
    allow_functions: bool = True,
) -> tuple[int, int]:
    """`(overflow functions, wrapper conditionals)` this order would cost, over
    the whole overflow chain. This is the objective the scheduler minimises:
    functions first (each one is a whole extra importable), then wrappers.

    With `allow_functions=False` there is no function to carve into, so the
    first term becomes `leftover expressions` instead: an order that fits is
    the difference between a working build and an `ActionLimitError`, and
    wrappers are free, so the scheduler spends them to drive leftover to zero.

    Pass `memo` when costing many orders of the same expressions: the counts are
    keyed by expression identity, which reordering does not change, so the
    flatten behind them happens once instead of once per candidate.

    The cost comes from running the real fixer rather than a model of it. An
    estimate that drifts from what `fix_action_limits` actually does lets the
    scheduler pick an order it believes is cheaper and is not - the trailing
    trigger alone has three placements and a fallback that pushes expressions
    back into the overflow.
    """
    from .actions.function import Function
    from .expression.condition.conditional_expression import ConditionalExpression

    if memo is None:
        memo = {}
    functions = 0
    wrappers = 0
    remaining = expressions
    current: ImportableKind = importable

    while True:
        original = {id(expression) for expression in remaining}
        result, rest = fix_action_limits(
            remaining,
            function_if_exceeds=Function('overflow') if allow_functions else None,
            importable=current,
            memo=memo,
            check_conditions=False,
        )
        wrappers += sum(
            1
            for expression in result
            if id(expression) not in original
            and isinstance(expression, ConditionalExpression)
        )
        if not rest:
            break
        if not allow_functions:
            return len(rest), wrappers
        functions += 1
        remaining = rest
        # Overflow always lands in a function block, whatever the original was.
        current = 'functions'

    return functions, wrappers


def fix_action_limits(
    expressions: list['Expression'],
    *,
    nesting_possible: bool = True,
    function_if_exceeds: 'Function | None' = None,
    always_in_conditional: bool = False,
    importable: ImportableKind = 'functions',
    memo: dict[int, ActionCounts] | None = None,
    check_conditions: bool = True,
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

    if check_conditions:
        check_all_condition_limits(expressions)

    if memo is None:
        memo = {}
    items, index, global_counter = plan_packing(
        expressions,
        nesting_possible=nesting_possible,
        always_in_conditional=always_in_conditional,
        importable=importable,
        memo=memo,
    )

    result: list[Expression] = []
    for kind, group in items:
        if kind == 'wrap':
            result.append(
                ConditionalExpression(
                    conditions=[],
                    mode=ConditionalMode.ALL,
                    if_expressions=group,
                ),
            )
        else:
            result.append(group[0])

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
