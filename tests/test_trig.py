import math
import random
import re

from pyhtsw import Container, ExecutionContext, PlayerStat
from pyhtsw.expression.binary_expression import BinaryExpression
from pyhtsw.expression.condition.conditional_expression import ConditionalExpression
from pyhtsw.ext import (
    approximate_acos,
    approximate_asin,
    approximate_atan,
    approximate_atan2,
    approximate_cos,
    approximate_exp,
    approximate_hypot,
    approximate_ln,
    approximate_log10,
    approximate_pow,
    approximate_sin,
    approximate_tan,
)

random.seed(20260821)


def run_one(build, put_values):
    with ExecutionContext() as ctx:
        stats = {name: PlayerStat(name).as_double() for name in put_values}
        out = PlayerStat('out').as_double()
        for name, v in put_values.items():
            ctx.put(stats[name], v)
        build(stats, out)
    return float(ctx.get_raw(out))


for _ in range(24):
    angle = random.uniform(-720.0, 720.0)
    got_sin = run_one(lambda s, o: approximate_sin(s['a'], assign_to=o), {'a': angle})
    got_cos = run_one(lambda s, o: approximate_cos(s['a'], assign_to=o), {'a': angle})
    assert abs(got_sin - math.sin(math.radians(angle))) < 0.01, (angle, got_sin)
    assert abs(got_cos - math.cos(math.radians(angle))) < 0.01, (angle, got_cos)

for angle in (0.0, 90.0, -90.0, 180.0, 270.0, 360.0, -540.0):
    got_sin = run_one(lambda s, o: approximate_sin(s['a'], assign_to=o), {'a': angle})
    got_cos = run_one(lambda s, o: approximate_cos(s['a'], assign_to=o), {'a': angle})
    assert abs(got_sin - math.sin(math.radians(angle))) < 0.01, (angle, got_sin)
    assert abs(got_cos - math.cos(math.radians(angle))) < 0.01, (angle, got_cos)


for angle in (-89.0, -60.0, -30.0, 0.0, 10.0, 45.0, 75.0, 89.0, 120.0, 200.0, -400.0):
    got = run_one(lambda s, o: approximate_tan(s['a'], assign_to=o), {'a': angle})
    want = math.tan(math.radians(angle))
    assert abs(got - want) < 0.01 * max(1.0, abs(want)), (angle, got, want)


for y, x in (
    (1.0, 1.0),
    (2.0, 1.0),
    (1.0, -1.0),
    (-1.0, -1.0),
    (-2.0, 1.0),
    (0.5, 3.0),
    (-3.0, -0.5),
    (1.0, 0.0),
    (-1.0, 0.0),
    (0.0, 1.0),
    (0.0, -1.0),
    (0.0, 0.0),
    (25000.0, -12345.0),
):
    got = run_one(
        lambda s, o: approximate_atan2(s['y'], s['x'], assign_to=o),
        {'y': y, 'x': x},
    )
    want = math.degrees(math.atan2(y, x)) if (y, x) != (0.0, 0.0) else 0.0
    assert abs(got - want) < 0.1, (y, x, got, want)

for _ in range(24):
    y = random.uniform(-50.0, 50.0)
    x = random.uniform(-50.0, 50.0)
    got = run_one(
        lambda s, o: approximate_atan2(s['y'], s['x'], assign_to=o),
        {'y': y, 'x': x},
    )
    want = math.degrees(math.atan2(y, x))
    assert abs(got - want) < 0.1, (y, x, got, want)

# Literal-x and literal-y forms.
got = run_one(lambda s, o: approximate_atan2(s['y'], 1.0, assign_to=o), {'y': 3.0})
assert abs(got - math.degrees(math.atan2(3.0, 1.0))) < 0.1, got
got = run_one(lambda s, o: approximate_atan2(-2.0, s['x'], assign_to=o), {'x': -1.0})
assert abs(got - math.degrees(math.atan2(-2.0, -1.0))) < 0.1, got


for v in (-100.0, -5.0, -1.0, -0.3, 0.0, 0.3, 1.0, 5.0, 100.0):
    got = run_one(lambda s, o: approximate_atan(s['z'], assign_to=o), {'z': v})
    want = math.degrees(math.atan(v))
    assert abs(got - want) < 0.1, (v, got, want)


for v in (-0.95, -0.7, -0.3, 0.0, 0.2, 0.5, 0.8, 0.95):
    got = run_one(lambda s, o: approximate_asin(s['z'], assign_to=o), {'z': v})
    want = math.degrees(math.asin(v))
    assert abs(got - want) < 0.6, (v, got, want)
    got = run_one(lambda s, o: approximate_acos(s['z'], assign_to=o), {'z': v})
    want = math.degrees(math.acos(v))
    assert abs(got - want) < 0.6, (v, got, want)


for v in (-20.0, -5.0, -1.0, -0.1, 0.0, 0.1, 1.0, 2.5, 5.0, 10.0, 20.0):
    got = run_one(lambda s, o: approximate_exp(s['x'], assign_to=o), {'x': v})
    want = math.exp(v)
    assert abs(got - want) < 0.001 * max(1.0, want), (v, got, want)


for v in (0.001, 0.1, 0.5, 1.0, 2.0, 10.0, 123.456, 1e4, 1e6, 9e8):
    got = run_one(lambda s, o: approximate_ln(s['x'], assign_to=o), {'x': v})
    assert abs(got - math.log(v)) < 0.002, (v, got, math.log(v))
got = run_one(lambda s, o: approximate_log10(s['x'], assign_to=o), {'x': 1000.0})
assert abs(got - 3.0) < 0.002, got


for b, e in ((2.0, 10), (3.0, 5), (2.0, -3), (1.5, 0), (-2.0, 3), (2.0, 62)):
    got = run_one(
        lambda s, o, _e=e: approximate_pow(s['b'], _e, assign_to=o),
        {'b': b},
    )
    want = b**e
    assert abs(got - want) < 0.001 * max(1.0, abs(want)), (b, e, got, want)
for b, e in ((2.0, 0.5), (10.0, 1.5), (2.7, 3.3), (100.0, -0.5)):
    got = run_one(
        lambda s, o: approximate_pow(s['b'], s['e'], assign_to=o),
        {'b': b, 'e': e},
    )
    want = b**e
    assert abs(got - want) < 0.005 * max(1.0, abs(want)), (b, e, got, want)


for x, y in ((3.0, 4.0), (100.0, 0.5), (0.7, 0.7)):
    got = run_one(
        lambda s, o: approximate_hypot(s['x'], s['y'], assign_to=o), {'x': x, 'y': y}
    )
    want = math.hypot(x, y)
    assert abs(got - want) < 0.01 * max(1.0, want), (x, y, got, want)
got = run_one(
    lambda s, o: approximate_hypot(s['x'], s['y'], s['z'], assign_to=o),
    {'x': 1.0, 'y': 2.0, 'z': 2.0},
)
assert abs(got - 3.0) < 0.01, got


def counts_of(build) -> tuple[int, int]:
    with Container() as container:
        stats = {
            name: PlayerStat(name).as_double()
            for name in ('a', 'y', 'x', 'z', 'b', 'e')
        }
        build(stats, PlayerStat('out').as_double())
    counts = container.expression_counts(nested=True)
    return (
        counts.get(ConditionalExpression, 0),
        counts.get(BinaryExpression, 0),
    )


assert counts_of(lambda s, o: approximate_sin(s['a'], assign_to=o)) == (0, 24)
assert counts_of(lambda s, o: approximate_cos(s['a'], assign_to=o)) == (0, 24)
assert counts_of(
    lambda s, o: approximate_sin(s['a'], assign_to=o, certain_x_in_range=90),
) == (0, 8)
assert counts_of(lambda s, o: approximate_tan(s['a'], assign_to=o)) == (0, 21)
assert counts_of(lambda s, o: approximate_exp(s['x'], assign_to=o)) == (0, 20)
assert counts_of(lambda s, o: approximate_atan2(s['y'], s['x'], assign_to=o)) == (2, 55)
assert counts_of(lambda s, o: approximate_atan(s['z'], assign_to=o)) == (1, 41)
assert counts_of(lambda s, o: approximate_ln(s['x'], assign_to=o)) == (3, 76)
assert counts_of(lambda s, o: approximate_pow(s['b'], 10, assign_to=o)) == (0, 6)


with Container() as container:
    for _i in range(4):
        approximate_sin(
            PlayerStat('a').as_double(),
            assign_to=PlayerStat(f'o{_i}').as_double(),
        )
_names = set(re.findall(r'tmp\d+', container.into_htsl()))
assert len(_names) <= 3, _names


with ExecutionContext(ignore_action_limits=True) as ctx:
    for _i in range(16):
        ctx.put(PlayerStat(f'tmp{_i}'), 999_999 + _i, ignore_warning=True)
    for _i in range(4):
        ctx.put(PlayerStat(f'hw{_i}_0'), -12345, ignore_warning=True)
        ctx.put(PlayerStat(f'hw{_i}_500'), -54321, ignore_warning=True)
        ctx.put(PlayerStat(f'sw{_i}_0'), 'garbage', ignore_warning=True)

    _angle = PlayerStat('ang').as_double()
    ctx.put(_angle, 37.0)
    _s = PlayerStat('cs').as_double()
    _c = PlayerStat('cc').as_double()
    _h = PlayerStat('ch').as_double()
    _r = PlayerStat('cr').as_double()
    approximate_sin(_angle, assign_to=_s)
    approximate_cos(_angle, assign_to=_c)
    # chain: hypot of the pair is 1, atan2 recovers the angle
    approximate_hypot(_s, _c, assign_to=_h)
    approximate_atan2(_s, _c, assign_to=_r)

    def check_chain() -> None:
        # The pair's ~0.008 amplitude error propagates through atan2 as up to
        # ~0.6 degrees; the chain checks composition, not fresh accuracy.
        assert abs(float(ctx.get_raw(_h)) - 1.0) < 0.02, ctx.get_raw(_h)
        assert abs(float(ctx.get_raw(_r)) - 37.0) < 0.75, ctx.get_raw(_r)

    ctx.assert_all(check_chain)
