import math

from pyhtsw import (
    Container,
    EmulatedHouse,
    IfAll,
    Item,
    PlayerStat,
    chat,
    disable_global_export,
)
from pyhtsw.ext import (
    Block,
    Box,
    RayTarget,
    Sphere,
    create_position_raycast,
)
from pyhtsw.placeholders.player import (
    PlayerPositionPitch,
    PlayerPositionX,
    PlayerPositionY,
    PlayerPositionYaw,
    PlayerPositionZ,
)

disable_global_export()


def stand(
    house: EmulatedHouse,
    x: float = 0.5,
    y: float = 0.0,
    z: float = 0.5,
    *,
    yaw: float = 0.0,
    pitch: float = 0.0,
) -> None:
    """Place the caster. yaw=0 looks towards +Z, pitch=90 looks straight down."""
    house.put(PlayerPositionX, x, ignore_warning=True)
    house.put(PlayerPositionY, y, ignore_warning=True)
    house.put(PlayerPositionZ, z, ignore_warning=True)
    house.put(PlayerPositionYaw, yaw, ignore_warning=True)
    house.put(PlayerPositionPitch, pitch, ignore_warning=True)


# === The block dead ahead is hit; the ones beside, behind and above are not.
# The ray runs along +Z with look.x and look.y both exactly zero, which is the
# case the slab reciprocal has to survive. ===
with EmulatedHouse() as house:
    stand(house)
    ray = create_position_raycast(
        'Ahead',
        [
            (0, 1, 5),  # dead ahead
            (3, 1, 5),  # three blocks to the side
            (0, 1, -5),  # behind
            (0, 8, 5),  # far above the ray
        ],
    )
    ray.trigger()

assert int(house.get_raw(ray.index)) == 0, house.get_raw(ray.index)
assert abs(float(house.get_raw(ray.distance)) - 5.0) < 0.01, house.get_raw(ray.distance)


# === Closest wins, whatever order the positions are listed in. ===
with EmulatedHouse() as house:
    stand(house)
    ray = create_position_raycast('Closest', [(0, 1, 9), (0, 1, 3), (0, 1, 6)])
    ray.trigger()

assert int(house.get_raw(ray.index)) == 1, house.get_raw(ray.index)
assert abs(float(house.get_raw(ray.distance)) - 3.0) < 0.01, house.get_raw(ray.distance)


# === max_distance rejects everything past it, and a total miss leaves index at
# -1 with distance parked on the cap. ===
with EmulatedHouse() as house:
    stand(house)
    ray = create_position_raycast('Capped', [(0, 1, 20)], max_distance=8.0)
    ray.trigger()

assert int(house.get_raw(ray.index)) == -1, house.get_raw(ray.index)

with EmulatedHouse() as house:
    stand(house)
    ray = create_position_raycast('Uncapped', [(0, 1, 20)], max_distance=None)
    ray.trigger()

assert int(house.get_raw(ray.index)) == 0, house.get_raw(ray.index)


# === Looking straight down finds the block under the caster's feet. ===
with EmulatedHouse() as house:
    stand(house, y=10.0, pitch=90.0)
    ray = create_position_raycast('Down', [(0, 9, 0), (0, 20, 0)])
    ray.trigger()

assert int(house.get_raw(ray.index)) == 0, house.get_raw(ray.index)


# === A diagonal ray: yaw 45 looks towards -X/+Z, so the block on that diagonal
# is hit and the one straight ahead is not. ===
with EmulatedHouse() as house:
    stand(house, yaw=45.0)
    ray = create_position_raycast('Diagonal', [(0, 1, 5), (-5, 1, 5)])
    ray.trigger()

assert int(house.get_raw(ray.index)) == 1, house.get_raw(ray.index)


# === Shapes: a sphere small enough to sit inside the block it replaces is
# missed by a ray that clears its centre, while the block is hit. ===
with EmulatedHouse() as house:
    stand(house)
    ray = create_position_raycast(
        'Shapes',
        [
            RayTarget(0.9, 1.9, 5.5, shape=Sphere(0.2)),  # centre is off the ray
            RayTarget(0.5, 1.62, 9.5, shape=Sphere(0.5)),  # centre is on the ray
        ],
    )
    ray.trigger()

assert int(house.get_raw(ray.index)) == 1, house.get_raw(ray.index)
assert abs(float(house.get_raw(ray.distance)) - 9.0) < 0.01, house.get_raw(ray.distance)


# === A Box is centred on its position, unlike a Block, and per-axis sizes make
# a slab: 9 wide in x, 1 tall, so the ray that misses a cube still hits it. ===
with EmulatedHouse() as house:
    stand(house)
    ray = create_position_raycast(
        'Slab',
        [
            RayTarget(4.0, 1.62, 5.0, shape=Box(1.0)),  # a metre-cube 3.5 aside
            RayTarget(4.0, 1.62, 7.0, shape=Box(9.0, 1.0, 1.0)),  # reaches back
        ],
    )
    ray.trigger()

assert int(house.get_raw(ray.index)) == 1, house.get_raw(ray.index)


# === Dynamic coordinates: a target whose position lives in stats moves with
# them, and mixes freely with constant ones. ===
block_z = PlayerStat('target/z').as_double()

with EmulatedHouse() as house:
    stand(house)
    house.put(block_z, 4.0, ignore_warning=True)
    ray = create_position_raycast('Dynamic', [(0, 1, 12), RayTarget(0, 1, block_z)])
    ray.trigger()

assert int(house.get_raw(ray.index)) == 1, house.get_raw(ray.index)
assert abs(float(house.get_raw(ray.distance)) - 4.0) < 0.01, house.get_raw(ray.distance)


# === Conditions gate a target without changing the geometry: the nearer block
# is skipped while its switch is off, so the farther one is reported. ===
switch = PlayerStat('switch').as_long()

with EmulatedHouse() as house:
    stand(house)
    house.put(switch, 0, ignore_warning=True)
    ray = create_position_raycast(
        'Gated',
        [
            RayTarget(0, 1, 3, conditions=switch == 1),
            (0, 1, 6),
        ],
    )
    ray.trigger()

assert int(house.get_raw(ray.index)) == 1, house.get_raw(ray.index)

with EmulatedHouse() as house:
    stand(house)
    house.put(switch, 1, ignore_warning=True)
    ray = create_position_raycast(
        'Ungated',
        [
            RayTarget(0, 1, 3, conditions=switch == 1),
            (0, 1, 6),
        ],
    )
    ray.trigger()

assert int(house.get_raw(ray.index)) == 0, house.get_raw(ray.index)


# === An explicit origin and direction detach the cast from the caster's eyes
# entirely — the same helper serves a projectile. ===
with EmulatedHouse() as house:
    stand(house, x=100.0, y=100.0, z=100.0)  # nowhere near the ray
    ray = create_position_raycast(
        'Projectile',
        [(0, 0, 5)],
        origin=(0.5, 0.5, 0.5),
        direction=(0.0, 0.0, 1.0),
    )
    ray.trigger()

assert int(house.get_raw(ray.index)) == 0, house.get_raw(ray.index)


# === compute_hit_point puts the point on the ray at `distance`. ===
with EmulatedHouse() as house:
    stand(house)
    ray = create_position_raycast('Point', [(0, 1, 5)], compute_hit_point=True)
    ray.trigger()

assert ray.hit_z is not None
assert abs(float(house.get_raw(ray.hit_z)) - 5.5) < 0.02, house.get_raw(ray.hit_z)


# === Callbacks: on_hit runs at top level (so it may branch), on_miss inside a
# conditional, and on_target_hit dispatches per position. ===
hit_flag = PlayerStat('cb/hit').as_long()
miss_flag = PlayerStat('cb/miss').as_long()
which = PlayerStat('cb/which').as_long()


with EmulatedHouse() as house:
    stand(house)

    def on_hit() -> None:
        hit_flag.value = 1
        with IfAll(ray.distance > 0.0):  # top level, so branching is allowed
            hit_flag.value = 2

    def on_miss() -> None:
        miss_flag.value = 1

    def on_target_hit(position: int, _target: object) -> None:
        which.value = 100 + position

    ray = create_position_raycast(
        'Callbacks',
        [(0, 1, 9), (0, 1, 4)],
        on_hit=on_hit,
        on_miss=on_miss,
        on_target_hit=on_target_hit,
    )
    ray.trigger()

assert int(house.get_raw(hit_flag)) == 2, house.get_raw(hit_flag)
assert int(house.get_raw(miss_flag)) == 0, house.get_raw(miss_flag)
assert int(house.get_raw(which)) == 101, house.get_raw(which)

with EmulatedHouse() as house:
    stand(house)

    def on_hit_2() -> None:
        hit_flag.value = 1

    def on_miss_2() -> None:
        miss_flag.value = 1

    ray = create_position_raycast(
        'Callbacks Miss',
        [(40, 1, 9)],
        on_hit=on_hit_2,
        on_miss=on_miss_2,
    )
    ray.trigger()

assert int(house.get_raw(hit_flag)) == 0, house.get_raw(hit_flag)
assert int(house.get_raw(miss_flag)) == 1, house.get_raw(miss_flag)


# === Pair CSE must not change what the cast computes. A grid shares partial
# sums across targets; with and without it the answer is identical. ===
GRID = [(x, 1, z) for x in range(-2, 3) for z in range(3, 8)]

for use_pairs in (True, False):
    with EmulatedHouse() as house:
        stand(house)
        ray = create_position_raycast(
            f'Grid {use_pairs}',
            GRID,
            pair_cse=use_pairs,
        )
        ray.trigger()
    hit = int(house.get_raw(ray.index))
    assert GRID[hit] == (0, 1, 3), (use_pairs, hit, GRID[hit])


# === The CSE plan is what makes a grid cheap: the per-axis offset from the ray
# origin is computed once per *distinct* coordinate value, not once per target.
# GRID is 5 x 1 x 5, so that is 11 offsets backing 25 targets. ===
with Container() as container:
    ray = create_position_raycast('Cost', GRID, shape=Block())
htsl = container.into_htsl()
assert 'pr/index' in htsl
offsets = sum(htsl.count(f'-= "%var.player/pr/pos/{axis} 0.0%D"') for axis in 'xyz')
assert offsets == 11, offsets
# One conditional per target keeps the nearest, and nothing else writes the index.
assert htsl.count('var "pr/index" = ') == len(GRID) + 1, htsl.count('var "pr/index" = ')


# === An empty position list is a mistake, not an empty cast. ===
try:
    with Container():
        create_position_raycast('Empty', [])
except ValueError:
    pass
else:
    raise AssertionError('expected a ValueError for an empty position list')


# === chat() keeps working inside a callback (nothing here is deferred oddly). ===
with Container() as container:
    ray = create_position_raycast(
        'Chatty',
        [(0, 1, 5)],
        on_hit=lambda result: chat(f'&aHit block {result.index} at {result.distance}'),
    )
assert 'pr/index' in container.into_htsl()


# === icon reaches the Function it creates. ===
with Container():
    ray = create_position_raycast('IconCast', [(0, 1, 5)], icon=Item('bow'))

assert ray.function.icon == Item('bow'), ray.function.icon


# === Oblique angles at long range. The projection identity needs |direction|²,
# and the look vector is only unit-length to three decimals; before that was
# divided out, a radius-1 sphere stopped registering past ~7 blocks at every
# yaw where sin is not exact. Aim dead centre and demand a hit at both shapes
# out to the default 64-block cap. ===
_ANGLES = (
    (0.0, 0.0),
    (80.0, 25.0),
    (-100.0, -25.0),
    (37.0, 0.0),
    (90.0, 0.0),
    (-125.0, 0.0),
    (37.0, 25.0),
    (0.0, -40.0),
    (45.0, 45.0),
    (13.0, -7.0),
)

for _shape, _label in ((Sphere(1.0), 'Sphere(1.0)'), (Box(2.0), 'Box(2.0)')):
    for _yaw, _pitch in _ANGLES:
        for _distance in (5.0, 10.0, 20.0, 40.0, 64.0):
            _yr, _pr = math.radians(_yaw), math.radians(_pitch)
            _direction = (
                -math.sin(_yr) * math.cos(_pr),
                -math.sin(_pr),
                math.cos(_yr) * math.cos(_pr),
            )
            _cx, _cy, _cz = (
                (0.5, 1.62, 0.5)[_k] + _direction[_k] * _distance for _k in range(3)
            )
            with EmulatedHouse() as house:
                stand(house, yaw=_yaw, pitch=_pitch)
                ray = create_position_raycast(
                    'Oblique',
                    [RayTarget(_cx, _cy, _cz)],
                    shape=_shape,
                    max_distance=None,
                )
                ray.trigger()
            assert int(house.get_raw(ray.index)) == 0, (
                _label,
                _yaw,
                _pitch,
                _distance,
                house.get_raw(ray.index),
            )
            _got = float(house.get_raw(ray.distance))
            assert abs(_got - _distance) < 0.1, (
                _label,
                _yaw,
                _pitch,
                _distance,
                _got,
            )
