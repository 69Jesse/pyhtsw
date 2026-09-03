from helpers import expect_exception

from pyhtsw import (
    Container,
    EmulatedHouse,
    GlobalStat,
    IfAll,
    PlayerStat,
)
from pyhtsw.execute.backend_type import cast_to_backend_long

# put/get round-trip for long
with EmulatedHouse() as house:
    x = PlayerStat('x').as_long()
    house.put(x, 42)

assert int(house.get(x)) == 42, house.get(x)


# put/get round-trip for double (use get_raw to avoid the emulator's 3-decimal
# string-rounding when reading doubles back through house.get).
with EmulatedHouse() as house:
    d = PlayerStat('d').as_double()
    house.put(d, 3.14159)

assert float(house.get_raw(d)) == 3.14159, house.get_raw(d)


# put/get round-trip for string
with EmulatedHouse() as house:
    s = PlayerStat('s').as_string()
    house.put(s, 'hello')

assert str(house.get(s)) == 'hello', house.get(s)


# Stat that wasn't put returns its default fallback (long: 0)
with EmulatedHouse() as house:
    x = PlayerStat('x').as_long()

assert int(house.get(x)) == 0, house.get(x)


# `with_fallback(N)` is honored by both `get` and `get_raw` when the stat hasn't been set
with EmulatedHouse() as house:
    x = PlayerStat('x').as_long().with_fallback(42)

assert int(house.get(x)) == 42, house.get(x)
assert int(house.get_raw(x)) == 42, house.get_raw(x)


# `house.put` overrides the fallback.
with EmulatedHouse() as house:
    x = PlayerStat('x').as_long().with_fallback(42)
    house.put(x, 7)

assert int(house.get(x)) == 7, house.get(x)


# Arithmetic propagates through execution
with EmulatedHouse() as house:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    house.put(x, 10)
    y.value = x + 5

assert int(house.get(y)) == 15, house.get(y)


# GlobalStat works in execution too
with EmulatedHouse() as house:
    g = GlobalStat('shared').as_long()
    house.put(g, 7)

assert int(house.get(g)) == 7, house.get(g)


# Conditional execution: branch is taken when the condition holds
with EmulatedHouse() as house:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    house.put(x, 10)
    with IfAll(x > 5):
        y.value = 1
    # else: y stays at 0

assert int(house.get(y)) == 1, house.get(y)


# Conditional execution: branch is skipped when the condition fails
with EmulatedHouse() as house:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    house.put(x, 1)
    with IfAll(x > 5):
        y.value = 1

assert int(house.get(y)) == 0, house.get(y)


# Failing assert raises AssertionError that escapes the context manager
with expect_exception(AssertionError):
    with EmulatedHouse() as house:
        x = PlayerStat('x').as_long()
        house.put(x, 5)
        house.assert_all(x == 10)


# assert_any: passes when at least one condition holds
with EmulatedHouse() as house:
    x = PlayerStat('x').as_long()
    house.put(x, 5)
    house.assert_any(x == 1, x == 5, x == 99)


# assert_any with a callable that returns None is a no-op (skipped)
with EmulatedHouse() as house:
    x = PlayerStat('x').as_long()
    house.put(x, 5)

    def maybe_check() -> None:
        return None  # callable returns None, condition is discarded

    # Vacuously passes since the only condition is discarded.
    house.assert_any(maybe_check, x == 5)


# Sanity: EmulatedHouse can also produce HTSL via into_htsl
with Container() as container:
    x = PlayerStat('x').as_long()
    x.value = 1

assert container.into_htsl() == 'var "x" = 1 true', container.into_htsl()


# Storage path: each assignment substitutes the rhs once. Chained-placeholder
# strings stay one level deep when stored (here `c` keeps `%var.player/s0%`,
# not 5). An intentional self-assignment then routes through get()'s fullmatch
# loop, which DOES chase the chain transitively, so c ends up holding the
# resolved numeric value 5.
with EmulatedHouse() as house:
    s0 = PlayerStat('s0').with_auto_unset(False)
    s0.value = 5
    a = PlayerStat('a').with_auto_unset(False)
    a.value = '%var.player/s'
    b = PlayerStat('b').with_auto_unset(False)
    b.value = 0

    c = PlayerStat('c').with_auto_unset(False)
    c.value = '%var.player/a%%var.player/b%%'

    # Mid-execution check: at this point c stores the once-substituted
    # placeholder string. get_raw bypasses substitution so we see the literal.
    def check_before_self_assign() -> None:
        assert str(house.get_raw(c)) == '%var.player/s0%', house.get_raw(c)

    house.run(check_before_self_assign)

    # Intentional self-assign: rhs renders as bare `%var.player/c%` (no type
    # suffix because fix_type_compatibility is skipped), and get()'s fullmatch
    # loop chases the placeholder chain `c` -> `%var.player/s0%` -> `s0` -> 5.
    c.set(c, is_intentional_self_assignment=True)

# Emitted HTSL keeps the bare placeholder form for the self-assign.
assert 'var "c" = %var.player/c%' in house.into_htsl(), house.into_htsl()

# After execution: c now holds the resolved value, not the placeholder.
assert int(house.get_raw(c)) == 5, house.get_raw(c)


# Stat-to-stat assignment preserves the rhs's native type, but a Python-`str`
# rhs (which renders to HTSL as quoted, `var "c" = "%var.player/a%"`) routes
# through string-mode → substitute → cast, so `c.value = f"{a}"` stores long
# 123 even though `a` is double 123.0.
with EmulatedHouse() as house:
    a = PlayerStat('a').with_auto_unset(False)
    a.value = 123.0
    b = PlayerStat('b').with_auto_unset(False)
    b.value = a
    c = PlayerStat('c').with_auto_unset(False)
    c.value = f'{a}'

assert 'var "b" = %var.player/a%' in house.into_htsl(), house.into_htsl()
assert 'var "c" = "%var.player/a%"' in house.into_htsl(), house.into_htsl()
assert isinstance(house.get_raw(b), float), type(house.get_raw(b))
assert house.get_raw(b) == 123.0, house.get_raw(b)
# htsw renders a whole double as `123.0` (formatNumber of toFixed(4)), so the
# one-pass string re-parses as a double, not a long.
assert isinstance(house.get_raw(c), float), type(house.get_raw(c))
assert house.get_raw(c) == 123.0, house.get_raw(c)


# === Long precision: matches Java's Long, no float64 round-trip drift ===
#
# Java's `long` is exactly 64 bits. The emulator must round-trip every
# representable long through house.get without losing precision — float64 only
# has ~53 bits of mantissa, so anything above 2**53 had been silently
# corrupted before cast_to_backend_long was fixed to try int() first.

# Boundary: exactly 2**53 round-trips cleanly via either path.
with EmulatedHouse() as house:
    x = PlayerStat('x').as_long()
    house.put(x, 2**53)

assert int(house.get(x)) == 2**53, house.get(x)


# Above the float53 line: values that float64 cannot represent exactly.
for _v in (2**53 + 1, 2**60 - 1, 22551026487849030, 9223372036854775807):
    with EmulatedHouse() as house:
        x = PlayerStat('x').as_long()
        house.put(x, _v)

    got = int(house.get(x))
    assert got == _v, f'long round-trip lost precision: got {got}, want {_v}'


# Java long min / max boundaries.
for _v in (-(2**63), 2**63 - 1):
    with EmulatedHouse() as house:
        x = PlayerStat('x').as_long()
        house.put(x, _v)

    got = int(house.get(x))
    assert got == _v, f'long boundary lost precision: got {got}, want {_v}'


# Bitwise ops on large packed longs preserve precision (the use-case that
# motivated the fix — IntStack packs many small ints into one long).
with EmulatedHouse() as house:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    # Packed value [70, 60, 50, 40, 30, 20] at 10 bits per slot.
    packed = 70 + 60 * 1024 + 50 * 2**20 + 40 * 2**30 + 30 * 2**40 + 20 * 2**50
    house.put(x, packed)
    y.value = x & 1023

assert int(house.get(y)) == 70, house.get(y)


# Right-shift through the high bits keeps the bit pattern intact.
with EmulatedHouse() as house:
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    house.put(x, 1 << 60)
    y.value = x >> 60

assert int(house.get(y)) == 1, house.get(y)


# Decimal/exponent strings still parse via the float fallback (so existing
# behavior on non-integer literals is preserved).

assert (x := cast_to_backend_long('1.5')) is not None and int(x) == 1
assert (x := cast_to_backend_long('2.9')) is not None and int(x) == 2
assert (x := cast_to_backend_long('1e3')) is not None and int(x) == 1000
assert cast_to_backend_long('garbage') is None
assert (x := cast_to_backend_long('')) is not None and int(x) == 0
assert (x := cast_to_backend_long('1,000')) is not None and int(x) == 1000
# Out-of-range integer string returns None instead of clipping.
assert cast_to_backend_long('9223372036854775808') is None  # 2**63
assert cast_to_backend_long('-9223372036854775809') is None  # -(2**63) - 1
