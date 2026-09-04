from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from pyhtsw.actions.flow import IfAll, exit_function, trigger_function
from pyhtsw.checkable import Checkable
from pyhtsw.declarations.function import Function, function
from pyhtsw.declarations.item import Item
from pyhtsw.expression.condition.condition import Condition
from pyhtsw.ext.look_vector import (
    DIRECTION_SCALE,
    approximate_look_vector,
    emit_direction_squared,
)
from pyhtsw.placeholders.player import PlayerPositionX, PlayerPositionY, PlayerPositionZ
from pyhtsw.stats.player_stat import PlayerStat
from pyhtsw.stats.temporary_stat import TemporaryStat
from pyhtsw.utils.callback import call_with_optional_args

__all__ = (
    'Block',
    'Box',
    'PositionRaycastResult',
    'RayTarget',
    'Shape',
    'Sphere',
    'create_position_raycast',
)


Coord = Checkable | int | float
ConditionsArg = (
    Condition | Iterable[Condition] | Callable[[], Condition | Iterable[Condition]]
)
HitCallback = Callable[['PositionRaycastResult'], Any] | Callable[[], Any]
TargetCallback = Callable[[int, 'RayTarget'], Any]

# Below this the ray is parallel enough to a slab plane that its reciprocal is
# meaningless; nudging keeps the division finite and the sign intact. Chosen to
# survive the emulator's 3-decimal placeholder rounding.
EPSILON = 0.001
NO_LIMIT = 1_000_000.0


class Shape:
    """Base for a target's hitbox. Use `Sphere`, `Box` or `Block`."""

    def axes(self) -> tuple[tuple[float, float], ...]:
        """Per axis, the box centre's offset from the position and its half
        extent. Only meaningful for the box family."""
        raise NotImplementedError


@dataclass(frozen=True)
class Sphere(Shape):
    """A ball around the position."""

    radius: float = 0.5

    def axes(self) -> tuple[tuple[float, float], ...]:
        return ((0.0, self.radius),) * 3


@dataclass(frozen=True)
class Box(Shape):
    """An axis-aligned box centred on the position. One size is a cube; three
    give per-axis sizes (a slab, a wall, a column)."""

    size_x: float = 1.0
    size_y: float | None = None
    size_z: float | None = None

    def axes(self) -> tuple[tuple[float, float], ...]:
        y = self.size_x if self.size_y is None else self.size_y
        z = self.size_x if self.size_z is None else self.size_z
        return tuple((0.0, size / 2.0) for size in (self.size_x, y, z))


@dataclass(frozen=True)
class Block(Shape):
    """The Minecraft block whose minimum corner is the position — `(10, 64, 5)`
    spans [10,11] x [64,65] x [5,6], matching block coordinates as written."""

    size: float = 1.0

    def axes(self) -> tuple[tuple[float, float], ...]:
        return ((self.size / 2.0, self.size / 2.0),) * 3


@dataclass(frozen=True)
class RayTarget:
    """One position the ray is tested against. Coordinates may be Python
    numbers or `Checkable`s, mixed freely."""

    x: Coord
    y: Coord
    z: Coord
    shape: Shape | None = None
    conditions: ConditionsArg | None = None
    data: Any = None


PositionArg = RayTarget | Sequence[Coord]


@dataclass(frozen=True)
class PositionRaycastResult:
    """A built position raycast: its `Function`, a `trigger` to fire it, the
    resolved targets, and the output stats.

    `index` is the 0-based index of the closest target hit, or -1 on a miss.
    `distance` is that target's centre projected onto the ray. Both are
    PlayerStats — everything runs in the caster's own context, so two players
    casting in the same tick never see each other's values.
    """

    function: Function
    trigger: Callable[[], None]
    targets: tuple[RayTarget, ...]
    index: PlayerStat
    distance: PlayerStat
    look_x: PlayerStat
    look_y: PlayerStat
    look_z: PlayerStat
    origin_x: PlayerStat
    origin_y: PlayerStat
    origin_z: PlayerStat
    hit_x: PlayerStat | None
    hit_y: PlayerStat | None
    hit_z: PlayerStat | None


def _gather_conditions(conditions: ConditionsArg | None) -> list[Condition]:
    if conditions is None:
        return []
    if not isinstance(conditions, Condition) and callable(conditions):
        conditions = conditions()
    if isinstance(conditions, Condition):
        return [conditions]
    return list(conditions)


def _into_target(position: PositionArg, default_shape: Shape) -> RayTarget:
    if isinstance(position, RayTarget):
        if position.shape is not None:
            return position
        return RayTarget(
            position.x,
            position.y,
            position.z,
            default_shape,
            position.conditions,
            position.data,
        )
    x, y, z = position
    return RayTarget(x, y, z, default_shape)


# A centre is shared between targets when it is the same constant, or the same
# Checkable read with the same offset — never across the two.
def _centre_key(value: Coord, offset: float) -> tuple[object, ...]:
    if isinstance(value, Checkable):
        return ('stat', value.into_hashable(), offset)
    return ('const', float(value) + offset)


def _choose_pair(
    keys_per_target: list[tuple[tuple[object, ...], ...]],
) -> tuple[int, int] | None:
    count = len(keys_per_target)
    best_cost = 3 * count
    best_pair: tuple[int, int] | None = None
    for pair in ((0, 1), (0, 2), (1, 2)):
        i, j = pair
        distinct = len({(keys[i], keys[j]) for keys in keys_per_target})
        cost = 2 * distinct + 2 * count
        if cost < best_cost:
            best_cost = cost
            best_pair = pair
    return best_pair


def _unique_pairs(
    keys_per_target: list[tuple[tuple[object, ...], ...]],
    pair: tuple[int, int],
) -> list[tuple[tuple[object, ...], tuple[object, ...]]]:
    i, j = pair
    seen: dict[tuple[tuple[object, ...], tuple[object, ...]], None] = {}
    for keys in keys_per_target:
        seen[keys[i], keys[j]] = None
    return list(seen)


def create_position_raycast(
    name: str,
    positions: Iterable[PositionArg],
    *,
    shape: Shape | None = None,
    stat_prefix: str = 'pr/',
    icon: Item | None = None,
    origin: Sequence[Coord] | None = None,
    direction: Sequence[Coord] | None = None,
    eye_height: float = 1.62,
    max_distance: float | None = 64.0,
    conditions: ConditionsArg | None = None,
    on_hit: HitCallback | None = None,
    on_miss: HitCallback | None = None,
    on_target_hit: TargetCallback | None = None,
    compute_hit_point: bool = False,
    pair_cse: bool = True,
) -> PositionRaycastResult:
    """Build a raycast against a fixed list of positions and return a
    `PositionRaycastResult`.

    Unlike `create_raycast`, nothing fans out to other players: the position
    list is known in Python, so the whole cast unrolls into one function that
    runs in the caster's own context.

    Only the *closest* target is reported. `result.index` is its index in
    `positions` (-1 = miss) and `result.distance` is its centre projected onto
    the ray — the same quantity `create_raycast` reports.

    Parameters
    ----------
    positions:
        `(x, y, z)` tuples, or `RayTarget`s when a position needs its own
        shape, its own extra conditions, or a `data` payload. Coordinates may
        be Python numbers or `Checkable`s in any mix.
    shape:
        Default hitbox for positions that do not carry one. `Block()` treats a
        position as the block at those coordinates; `Box(...)` centres a box on
        it; `Sphere(...)` uses a ball.
    icon:
        Item shown next to the created `Function` in Housing.
    origin / direction:
        `(x, y, z)` triples. Default to the caster's eyes (`eye_height` above
        their feet) and their look vector, which makes the helper serve a
        projectile just as well as a look ray. Hit tests hold for any
        `direction`, but `distance` and `max_distance` are measured in units of
        its length, so pass a unit vector for them to be in blocks.
    max_distance:
        Targets past this are ignored (None = no cap). This is the same
        comparison that tracks the closest hit, so it is free.
    conditions:
        Extra requirements every target must satisfy, evaluated in the caster's
        context. A `RayTarget` may add its own on top.
    on_hit / on_miss:
        Run once after the cast resolves. `on_hit` runs at top level, so it may
        open its own conditionals; `on_miss` runs *inside* one and may not —
        call a function from it if it needs to branch.
    on_target_hit:
        Called in Python as `on_target_hit(index, target)` for every target, to
        emit that target's own actions behind an `index == i` check. Like
        `on_miss`, its actions sit inside a conditional.
    compute_hit_point:
        Also write `result.hit_x/y/z`, the point on the ray at `distance`. Only
        written on a hit; after a miss they hold the previous cast's point,
        which is what `result.index` is for.
    pair_cse:
        Share two-axis partial sums when doing so costs fewer actions. Saves
        roughly one action per target on grid-shaped inputs, at two persistent
        temporaries per distinct axis pair.

    Cost
    ----
    Per target: one conditional, plus 5 actions for a box or 11 for a sphere.
    Per *distinct* coordinate value per axis: 4 actions (6 for a sphere, 8 for
    a box) — which is why a grid is far cheaper than its position count
    suggests. A box target spends 11 conditions of its conditional's budget and
    a sphere 3, so per-target `conditions` have 9 and 17 left respectively.
    """
    default_shape = Block() if shape is None else shape
    targets = tuple(_into_target(position, default_shape) for position in positions)
    if not targets:
        raise ValueError('create_position_raycast needs at least one position')

    def player_double(suffix: str) -> PlayerStat:
        return PlayerStat(f'{stat_prefix}{suffix}').as_double().with_auto_unset(False)

    def player_long(suffix: str) -> PlayerStat:
        return PlayerStat(f'{stat_prefix}{suffix}').as_long().with_auto_unset(False)

    look = (player_double('look/x'), player_double('look/y'), player_double('look/z'))
    org = (player_double('pos/x'), player_double('pos/y'), player_double('pos/z'))
    index = player_long('index')
    best = player_double('dist')
    hit = (
        (player_double('hit/x'), player_double('hit/y'), player_double('hit/z'))
        if compute_hit_point
        else (None, None, None)
    )

    centres: list[dict[tuple[object, ...], tuple[Coord, float]]] = [{}, {}, {}]
    squared: list[set[tuple[object, ...]]] = [set(), set(), set()]  # sphere only
    halves: list[dict[tuple[object, ...], set[float]]] = [{}, {}, {}]  # box only
    extents: list[set[float]] = [set(), set(), set()]

    target_keys: list[tuple[tuple[object, ...], ...]] = []
    target_axes: list[tuple[tuple[float, float], ...]] = []
    for target in targets:
        axes = target.shape.axes() if target.shape is not None else default_shape.axes()
        coords = (target.x, target.y, target.z)
        keys: list[tuple[object, ...]] = []
        for axis, (value, (offset, half)) in enumerate(zip(coords, axes, strict=True)):
            key = _centre_key(value, offset)
            centres[axis].setdefault(key, (value, offset))
            if isinstance(target.shape, Sphere):
                squared[axis].add(key)
            else:
                halves[axis].setdefault(key, set()).add(half)
                extents[axis].add(half)
            keys.append(key)
        target_keys.append(tuple(keys))
        target_axes.append(axes)

    any_box = any(extents)
    sphere_indexes = [
        i for i, target in enumerate(targets) if isinstance(target.shape, Sphere)
    ]
    projection_pair = _choose_pair(target_keys) if pair_cse else None
    square_pair = (
        _choose_pair([target_keys[i] for i in sphere_indexes])
        if pair_cse and sphere_indexes
        else None
    )

    @function(name, icon=icon)
    def cast_function() -> None:
        if direction is None:
            approximate_look_vector(
                assign_to_x=look[0],
                assign_to_y=look[1],
                assign_to_z=look[2],
            )
        else:
            for stat, value in zip(look, direction, strict=True):
                stat.value = value

        if origin is None:
            org[0].value = PlayerPositionX
            org[1].value = PlayerPositionY
            org[1].value += eye_height
            org[2].value = PlayerPositionZ
        else:
            for stat, value in zip(org, origin, strict=True):
                stat.value = value

        index.value = -1
        best.value = NO_LIMIT if max_distance is None else float(max_distance)

        inverse: dict[int, TemporaryStat] = {}
        extent_stats: dict[tuple[int, float], TemporaryStat] = {}
        if any_box:
            for axis in range(3):
                if not extents[axis]:
                    continue
                # A component of exactly 0 has no reciprocal; nudge it while
                # keeping its sign, which decides which slab face is the near one.
                with IfAll(look[axis] >= 0.0, look[axis] < EPSILON):
                    look[axis].value = EPSILON
                with IfAll(look[axis] < 0.0, look[axis] > -EPSILON):
                    look[axis].value = -EPSILON
                inv = TemporaryStat().as_double()
                inv.value = 1.0
                inv.value /= look[axis]
                inverse[axis] = inv
                # |1/l| scales a half extent into ray parameters, so the near
                # and far faces are `centre -+ extent` whichever way the ray runs.
                magnitude = TemporaryStat().as_double()
                magnitude.value = inv
                with IfAll(magnitude < 0.0):
                    magnitude.value *= -1
                for half in sorted(extents[axis]):
                    stat = TemporaryStat().as_double()
                    stat.value = magnitude
                    stat.value *= half
                    extent_stats[axis, half] = stat

        # The projection identity below needs |direction|^2, and the look
        # vector is only unit-length to the placeholder's three decimals.
        direction_squared: TemporaryStat | None = None
        if sphere_indexes:
            direction_squared = TemporaryStat().as_double()
            emit_direction_squared(
                direction_squared,
                TemporaryStat().as_double(),
                look,
            )

        projections: list[dict[tuple[object, ...], TemporaryStat]] = [{}, {}, {}]
        squares: list[dict[tuple[object, ...], TemporaryStat]] = [{}, {}, {}]
        lows: dict[tuple[int, tuple[object, ...], float], TemporaryStat] = {}
        highs: dict[tuple[int, tuple[object, ...], float], TemporaryStat] = {}
        for axis in range(3):
            for key, (value, offset) in centres[axis].items():
                offset_stat = TemporaryStat().as_double()
                if isinstance(value, Checkable):
                    offset_stat.value = value
                    if offset:
                        offset_stat.value += offset
                else:
                    offset_stat.value = float(value) + offset
                offset_stat.value -= org[axis]

                projection = TemporaryStat().as_double()
                projection.value = offset_stat
                projection.value *= look[axis]
                projections[axis][key] = projection

                if key in squared[axis]:
                    square = TemporaryStat().as_double()
                    square.value = offset_stat
                    square.value *= offset_stat
                    squares[axis][key] = square

                if key in halves[axis]:
                    scaled = TemporaryStat().as_double()
                    scaled.value = offset_stat
                    scaled.value *= inverse[axis]
                    for half in sorted(halves[axis][key]):
                        extent = extent_stats[axis, half]
                        low = TemporaryStat().as_double()
                        low.value = scaled
                        low.value -= extent
                        lows[axis, key, half] = low
                        high = TemporaryStat().as_double()
                        high.value = scaled
                        high.value += extent
                        highs[axis, key, half] = high

        def emit_pairs(
            per_axis: list[dict[tuple[object, ...], TemporaryStat]],
            pair: tuple[int, int],
            rows: list[tuple[tuple[object, ...], ...]],
        ) -> dict[tuple[tuple[object, ...], tuple[object, ...]], TemporaryStat]:
            i, j = pair
            shared: dict[
                tuple[tuple[object, ...], tuple[object, ...]],
                TemporaryStat,
            ] = {}
            for key_i, key_j in _unique_pairs(rows, pair):
                stat = TemporaryStat().as_double()
                stat.value = per_axis[i][key_i]
                stat.value += per_axis[j][key_j]
                shared[key_i, key_j] = stat
            return shared

        projection_pairs = (
            emit_pairs(projections, projection_pair, target_keys)
            if projection_pair is not None
            else {}
        )
        square_pairs = (
            emit_pairs(
                squares,
                square_pair,
                [target_keys[i] for i in sphere_indexes],
            )
            if square_pair is not None
            else {}
        )

        along = TemporaryStat().as_double()
        radial = TemporaryStat().as_double()
        limit = TemporaryStat().as_double()

        def emit_sum(
            destination: TemporaryStat,
            per_axis: list[dict[tuple[object, ...], TemporaryStat]],
            pair: tuple[int, int] | None,
            shared: dict[tuple[tuple[object, ...], tuple[object, ...]], TemporaryStat],
            keys: tuple[tuple[object, ...], ...],
        ) -> None:
            if pair is None:
                destination.value = per_axis[0][keys[0]]
                destination.value += per_axis[1][keys[1]]
                destination.value += per_axis[2][keys[2]]
                return
            i, j = pair
            rest = 3 - i - j
            destination.value = shared[keys[i], keys[j]]
            destination.value += per_axis[rest][keys[rest]]

        shared_conditions = _gather_conditions(conditions)
        for position, target in enumerate(targets):
            keys = target_keys[position]
            emit_sum(along, projections, projection_pair, projection_pairs, keys)
            checks: list[Condition]
            if isinstance(target.shape, Sphere):
                emit_sum(radial, squares, square_pair, square_pairs, keys)
                assert direction_squared is not None
                # |offset|^2 - along^2/|dir|^2 <= r^2, rearranged to avoid a
                # subtraction.
                limit.value = along
                limit.value *= along
                limit.value *= DIRECTION_SCALE
                limit.value /= direction_squared
                limit.value += target.shape.radius * target.shape.radius
                checks = [radial <= limit]
            else:
                sizes = [half for _, half in target_axes[position]]
                low = [lows[axis, keys[axis], sizes[axis]] for axis in range(3)]
                high = [highs[axis, keys[axis], sizes[axis]] for axis in range(3)]
                # max(low) <= min(high), as pairwise comparisons — no max/min
                # actions — plus min(high) >= 0 so the box is not behind us.
                checks = [
                    low[i] <= high[j] for i in range(3) for j in range(3) if i != j
                ]
                checks.extend(high[axis] >= 0.0 for axis in range(3))
            with IfAll(
                *checks,
                along >= 0.0,
                along < best,
                *shared_conditions,
                *_gather_conditions(target.conditions),
            ):
                best.value = along
                index.value = position

        has_hit_path = (
            on_hit is not None or on_target_hit is not None or compute_hit_point
        )
        if on_miss is not None or has_hit_path:
            with IfAll(index < 0):
                if on_miss is not None:
                    call_with_optional_args(on_miss, result, noun='on_miss')
                if has_hit_path:
                    exit_function()

        if compute_hit_point:
            for axis in range(3):
                point = hit[axis]
                assert point is not None
                point.value = look[axis]
                point.value *= best
                point.value += org[axis]

        if on_hit is not None:
            call_with_optional_args(on_hit, result, noun='on_hit')

        if on_target_hit is not None:
            for position, target in enumerate(targets):
                with IfAll(index == position):
                    on_target_hit(position, target)

    def trigger() -> None:
        trigger_function(cast_function)

    result = PositionRaycastResult(
        function=cast_function,
        trigger=trigger,
        targets=targets,
        index=index,
        distance=best,
        look_x=look[0],
        look_y=look[1],
        look_z=look[2],
        origin_x=org[0],
        origin_y=org[1],
        origin_z=org[2],
        hit_x=hit[0],
        hit_y=hit[1],
        hit_z=hit[2],
    )
    return result
