from bisect import insort
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyhtsw.limits import ImportableKind

    from pyhtsw.expression.condition.condition import Condition
    from pyhtsw.expression.expression import Expression


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

    @classmethod
    def of(
        cls,
        *,
        reads: 'Iterable[ResourceKey]' = (),
        writes: 'Iterable[ResourceKey]' = (),
        stream: Stream | None = None,
    ) -> 'Effects':
        return cls(frozenset(reads), frozenset(writes), stream, False)


BARRIER = Effects(frozenset(), frozenset(), None, True)


class _Collector:
    __slots__ = ('ok', 'reads', 'writes')

    def __init__(self) -> None:
        self.reads: set[ResourceKey] = set()
        self.writes: set[ResourceKey] = set()
        self.ok = True

    def checkable(self, value: object, *, write: bool = False) -> None:
        from pyhtsw.checkable import Checkable
        from pyhtsw.expression.binary_expression import BinaryExpression
        from pyhtsw.expression.compound_expression import CompoundExpression
        from pyhtsw.placeholders import PlaceholderCheckable
        from pyhtsw.stats.stat import Stat

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
            entry = type(value).htsw_meta.effects
            if entry is None:
                self.ok = False
                return
            self.reads.update(entry.reads)
            self.writes.update(entry.writes)
            if write:
                self.writes.update(entry.reads)
            return
        if isinstance(value, Checkable):
            self.ok = False

    def text(self, value: str) -> None:
        from pyhtsw.checkable import Checkable

        for ref in Checkable.iter_in_string(value):
            self.checkable(ref)

    def expression_fields(
        self,
        expression: 'Expression',
        *,
        treat_all_as_reads: bool = False,
    ) -> None:
        from pyhtsw.expression.binary_expression import BinaryExpression, BinaryOperator

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
        reads = type(condition).htsw_meta.reads
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
    from pyhtsw.expression.binary_expression import BinaryExpression
    from pyhtsw.expression.compound_expression import CompoundExpression
    from pyhtsw.expression.condition.conditional_expression import ConditionalExpression
    from pyhtsw.expression.unset_expression import UnsetExpression

    if type(expression).htsw_meta.control:
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
        entry = type(expression).htsw_meta.effects
        nested = expression.nested_expressions_refs()
        if entry is None and not nested:
            return BARRIER
        if entry is not None:
            collector.reads.update(entry.reads)
            collector.writes.update(entry.writes)
            stream = entry.stream
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
    from pyhtsw.actions.strict_order import strict_order_region_of

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
    from pyhtsw.expression.binary_expression import BinaryExpression
    from pyhtsw.stats.stat import Stat

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
    allow_functions: bool = True,
) -> tuple[int, int]:
    from pyhtsw.limits import packing_cost

    return packing_cost(
        expressions,
        importable=importable,
        memo=memo,
        allow_functions=allow_functions,
    )


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
    allow_functions: bool,
    budget: int,
) -> tuple[list[int], tuple[int, int]]:
    total = len(expressions)
    best_order = incumbent
    best_cost = incumbent_cost
    seen: set[frozenset[int]] = set()

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
                allow_functions,
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
# A block that cannot carve out an overflow function either fits or raises, so
# the extra seconds buy a working build rather than one fewer importable. Only
# blocks that would otherwise fail ever reach these.
NO_FUNCTION_EXACT_SEARCH_LIMIT = 16
NO_FUNCTION_EXACT_NODE_BUDGET = 200_000
NO_FUNCTION_LOCAL_SEARCH_LIMIT = 256
NO_FUNCTION_LOCAL_SEARCH_BUDGET = 4_000


def _local_improve(
    expressions: list['Expression'],
    preds: list[set[int]],
    order: list[int],
    cost: tuple[int, int],
    importable: 'ImportableKind',
    memo: dict,
    allow_functions: bool,
    budget: int,
) -> tuple[list[int], tuple[int, int]]:
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
                    allow_functions,
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
    allow_functions: bool = True,
) -> list['Expression'] | None:
    """Reorder a block so the limit fixer needs as few wrapper conditionals and
    overflow functions as possible. Returns `None` when the source order is
    already as good as anything reachable.

    With `allow_functions=False` the first cost term is leftover expressions
    instead, and the search runs on the wider budgets: fitting is the difference
    between a build and an `ActionLimitError`."""
    if len(expressions) < 2:
        return None

    # One memo for every candidate order: the action counts are keyed by
    # expression identity, so the flatten behind them survives reordering.
    memo: dict = {}
    base_cost = _packing_cost(expressions, importable, memo, allow_functions)
    if base_cost == (0, 0):
        return None

    if allow_functions:
        local_limit, local_budget = LOCAL_SEARCH_LIMIT, LOCAL_SEARCH_BUDGET
        exact_limit, exact_budget = EXACT_SEARCH_LIMIT, EXACT_NODE_BUDGET
    else:
        local_limit = NO_FUNCTION_LOCAL_SEARCH_LIMIT
        local_budget = NO_FUNCTION_LOCAL_SEARCH_BUDGET
        exact_limit = NO_FUNCTION_EXACT_SEARCH_LIMIT
        exact_budget = NO_FUNCTION_EXACT_NODE_BUDGET

    preds = build_dependencies(expressions)
    nestable = [_is_nestable(expression) for expression in expressions]
    identity = list(range(len(expressions)))

    order = _greedy_pack_order(preds, nestable)
    cost = _packing_cost(
        [expressions[index] for index in order],
        importable,
        memo,
        allow_functions,
    )
    if cost > base_cost:
        order, cost = identity, base_cost

    if len(expressions) <= local_limit:
        order, cost = _local_improve(
            expressions,
            preds,
            order,
            cost,
            importable,
            memo,
            allow_functions,
            local_budget,
        )

    if len(expressions) <= exact_limit:
        order, cost = _exact_pack_order(
            expressions,
            preds,
            importable,
            order,
            cost,
            memo,
            allow_functions,
            exact_budget,
        )

    if cost >= base_cost or order == identity:
        return None
    return [expressions[index] for index in order]
