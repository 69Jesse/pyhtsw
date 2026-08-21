import math
import random

from pyhtsw import Container, ExecutionContext, PlayerStat
from pyhtsw.expression.binary_expression import BinaryExpression
from pyhtsw.expression.condition.conditional_expression import ConditionalExpression
from pyhtsw.ext import (
    approximate_acos,
    approximate_asin,
    approximate_atan,
    approximate_atan2,
    approximate_cos,
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
    got_sin = run_one(
        lambda s, o: approximate_sin(s['a'], assign_to=o),
        {'a': angle},
    )
    got_cos = run_one(
        lambda s, o: approximate_cos(s['a'], assign_to=o),
        {'a': angle},
    )
    assert abs(got_sin - math.sin(math.radians(angle))) < 0.01, (angle, got_sin)
    assert abs(got_cos - math.cos(math.radians(angle))) < 0.01, (angle, got_cos)

for angle in (0.0, 90.0, -90.0, 180.0, 270.0, 360.0, -540.0):
    got_sin = run_one(lambda s, o: approximate_sin(s['a'], assign_to=o), {'a': angle})
    got_cos = run_one(lambda s, o: approximate_cos(s['a'], assign_to=o), {'a': angle})
    assert abs(got_sin - math.sin(math.radians(angle))) < 0.01, (angle, got_sin)
    assert abs(got_cos - math.cos(math.radians(angle))) < 0.01, (angle, got_cos)


for angle in (-60.0, -30.0, 0.0, 10.0, 45.0, 75.0, 120.0, 200.0):
    got = run_one(lambda s, o: approximate_tan(s['a'], assign_to=o), {'a': angle})
    want = math.tan(math.radians(angle))
    assert abs(got - want) < 0.05 * max(1.0, abs(want)), (angle, got, want)


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


def counts_of(build) -> tuple[int, int]:
    with Container() as container:
        stats = {name: PlayerStat(name).as_double() for name in ('a', 'y', 'x', 'z')}
        build(stats, PlayerStat('out').as_double())
    counts = container.expression_counts(nested=True)
    return (
        counts.get(ConditionalExpression, 0),
        counts.get(BinaryExpression, 0),
    )


assert counts_of(lambda s, o: approximate_sin(s['a'], assign_to=o)) == (0, 25)
assert counts_of(lambda s, o: approximate_cos(s['a'], assign_to=o)) == (0, 25)
assert counts_of(
    lambda s, o: approximate_sin(s['a'], assign_to=o, certain_x_in_range=90),
) == (0, 8)
# tan's one conditional is the fixer wrapping the 33-action overflow.
assert counts_of(lambda s, o: approximate_tan(s['a'], assign_to=o)) == (1, 33)
assert counts_of(
    lambda s, o: approximate_atan2(s['y'], s['x'], assign_to=o),
) == (3, 29)
assert counts_of(lambda s, o: approximate_atan(s['z'], assign_to=o)) == (2, 23)
