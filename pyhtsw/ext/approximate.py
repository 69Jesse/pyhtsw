import math
from typing import Literal, overload

from ..checkable import Checkable
from ..editable import Editable
from ..stats.stat import Stat
from ..stats.temporary_stat import TemporaryStat

__all__ = (
    'approximate_acos',
    'approximate_asin',
    'approximate_atan',
    'approximate_atan2',
    'approximate_cos',
    'approximate_exp',
    'approximate_hypot',
    'approximate_ln',
    'approximate_log10',
    'approximate_pow',
    'approximate_sin',
    'approximate_sin_cos',
    'approximate_sqrt',
    'approximate_tan',
)


_CARRY = 8


def _scratch(index: int) -> TemporaryStat:
    from ..container import get_current_container

    container = get_current_container()
    pool: list[TemporaryStat] = container.__dict__.setdefault(
        '_approximate_scratch',
        [],
    )
    while len(pool) <= index:
        pool.append(TemporaryStat())
    return pool[index]


def _double(index: int) -> Editable:
    return _scratch(index).as_double()


_STEP_OFFSET = 1_000_000_000


def _step_non_negative(slot: Editable, value: Checkable | float) -> Editable:
    slot.value = value
    slot.value += float(_STEP_OFFSET + 1)
    slot.cast_to_long()
    as_long = slot.as_long()
    as_long.value //= _STEP_OFFSET + 1
    return as_long


def _sign_into(slot: Editable, value: Checkable | float) -> None:
    as_long = _step_non_negative(slot, value)
    as_long.value *= 2
    as_long.value -= 1
    as_long.cast_to_double()


@overload
def approximate_sqrt(
    x: Checkable,
    *,
    assign_to: Editable,
    can_modify_x: Literal[False] = False,
) -> None: ...


@overload
def approximate_sqrt(
    x: Editable,
    *,
    assign_to: Editable,
    can_modify_x: Literal[True],
) -> None: ...


@overload
def approximate_sqrt(
    x: Editable,
    *,
    assign_to: Editable,
    can_modify_x: bool = False,
) -> None: ...


def approximate_sqrt(
    x: Checkable,
    *,
    assign_to: Editable,
    can_modify_x: bool = False,
) -> None:
    if x.equals(assign_to):
        raise ValueError('Cannot assign to the same stat as input')

    temp0 = _double(0)
    temp1 = _double(1)
    temp2 = _double(2)
    temp3 = _double(3)
    if not can_modify_x:
        x_or_temp4 = _double(4)
    else:
        assert isinstance(x, Editable)
        x_or_temp4 = x.as_double()
        if isinstance(x_or_temp4, Stat):
            x_or_temp4 = x_or_temp4.without_auto_unset()

    assign_to = assign_to.as_double()

    temp0.value = 3037000498.0
    temp0.value /= x
    temp0.value += 1.0

    x_or_temp4.value = x
    x_or_temp4.value *= temp0
    x_or_temp4.value *= temp0

    temp1.value = x_or_temp4
    temp1.value /= 537752656.0
    temp1.value += 880298.0

    temp2.value = x_or_temp4
    temp2.value /= temp1
    temp2.value += temp1

    temp1.value = x_or_temp4
    temp1.value /= temp2
    temp2.value *= 0.25
    temp2.value += temp1

    temp3.value = x_or_temp4
    temp3.value /= temp2
    temp3.value += temp2

    temp1.value = x_or_temp4
    temp1.value /= temp3
    temp3.value *= 0.25
    temp3.value += temp1

    assign_to.value = x_or_temp4
    assign_to.value /= temp3
    assign_to.value += temp3

    x_or_temp4.value /= assign_to
    assign_to.value /= 4.0
    assign_to.value += x_or_temp4

    assign_to.value += 1.0
    assign_to.value /= temp0


def _reduction_input(
    x: Checkable,
    can_modify_x: bool,
) -> Editable:
    if not can_modify_x:
        return _double(1)
    assert isinstance(x, Editable)
    x = x.as_double()
    if isinstance(x, Stat):
        x = x.without_auto_unset()
    return x


def _reduce_angle(
    x: Checkable,
    reduced: Editable,
    *,
    reduce: bool,
    with_parity: bool = True,
) -> Editable | None:
    if not reduce:
        reduced.value = x
        return None
    fold = _double(0)
    reduced.value = x
    reduced.value += 36090.0
    fold.value = reduced
    fold.value /= 180.0
    fold.cast_to_long()
    fold_long = fold.as_long()
    fold_sign: Editable | None = None
    if with_parity:
        # fold_sign = 1 - 2 * (fold mod 2): +1 on even folds, -1 on odd.
        fold_sign = _double(2)
        sign_long = fold_sign.as_long()
        sign_long.value = fold_long
        sign_long.value //= 2
        sign_long.value *= 2
        sign_long.value -= fold_long
        sign_long.value *= 2
        sign_long.value += 1
        sign_long.cast_to_double()
    fold.cast_to_double()
    fold.value *= 180.0
    reduced.value -= fold
    reduced.value -= 90.0
    return fold_sign


@overload
def approximate_sin_cos(
    x: Checkable,
    *,
    assign_to_sin: Editable,
    assign_to_cos: Editable,
    can_modify_x: Literal[False] = False,
    certain_x_in_range: Literal[90, 180] | None = None,
    sin_sign: Literal[1, -1] = 1,
    cos_sign: Literal[1, -1] = 1,
) -> None: ...


@overload
def approximate_sin_cos(
    x: Editable,
    *,
    assign_to_sin: Editable,
    assign_to_cos: Editable,
    can_modify_x: Literal[True],
    certain_x_in_range: Literal[90, 180] | None = None,
    sin_sign: Literal[1, -1] = 1,
    cos_sign: Literal[1, -1] = 1,
) -> None: ...


@overload
def approximate_sin_cos(
    x: Editable,
    *,
    assign_to_sin: Editable,
    assign_to_cos: Editable,
    can_modify_x: bool = False,
    certain_x_in_range: Literal[90, 180] | None = None,
    sin_sign: Literal[1, -1] = 1,
    cos_sign: Literal[1, -1] = 1,
) -> None: ...


def approximate_sin_cos(
    x: Checkable,
    *,
    assign_to_sin: Editable,
    assign_to_cos: Editable,
    can_modify_x: bool = False,
    certain_x_in_range: Literal[90, 180] | None = None,
    sin_sign: Literal[1, -1] = 1,
    cos_sign: Literal[1, -1] = 1,
) -> None:
    """sin and cos of x degrees together, sharing one range reduction."""
    x = x.as_double()
    temp0 = _double(3)
    x_or_temp1 = _reduction_input(x, can_modify_x)
    fold_sign = _reduce_angle(
        x,
        x_or_temp1,
        reduce=certain_x_in_range != 90,
    )

    assign_to_sin.value = x_or_temp1
    x_or_temp1.value *= x_or_temp1
    temp0.value = 32400.0
    temp0.value += x_or_temp1
    if cos_sign == 1:
        assign_to_cos.value = 32400.0
    else:
        assign_to_cos.value = -32400.0
    x_or_temp1.value *= 4.0
    if cos_sign == 1:
        assign_to_cos.value -= x_or_temp1
    else:
        assign_to_cos.value += x_or_temp1
    assign_to_cos.value /= temp0.value
    x_or_temp1.value *= assign_to_sin
    x_or_temp1.value /= 5508000.0

    if sin_sign == 1:
        assign_to_sin.value *= 0.017
        assign_to_sin.value -= x_or_temp1
    else:
        assign_to_sin.value *= -0.017
        assign_to_sin.value += x_or_temp1

    if fold_sign is not None:
        assign_to_sin.value *= fold_sign
        assign_to_cos.value *= fold_sign


def approximate_sin(
    x: Checkable,
    *,
    assign_to: Editable,
    can_modify_x: bool = False,
    certain_x_in_range: Literal[90, 180] | None = None,
    sign: Literal[1, -1] = 1,
) -> None:
    """sin(x degrees) alone: 7 actions past the shared range reduction."""
    x = x.as_double()
    r = _reduction_input(x, can_modify_x)
    fold_sign = _reduce_angle(x, r, reduce=certain_x_in_range != 90)

    assign_to.value = r
    r.value *= r
    r.value *= 4.0
    r.value *= assign_to
    r.value /= 5508000.0
    if sign == 1:
        assign_to.value *= 0.017
        assign_to.value -= r
    else:
        assign_to.value *= -0.017
        assign_to.value += r
    if fold_sign is not None:
        assign_to.value *= fold_sign


def approximate_cos(
    x: Checkable,
    *,
    assign_to: Editable,
    can_modify_x: bool = False,
    certain_x_in_range: Literal[90, 180] | None = None,
    sign: Literal[1, -1] = 1,
) -> None:
    """cos(x degrees) alone: 7 actions past the shared range reduction."""
    x = x.as_double()
    r = _reduction_input(x, can_modify_x)
    fold_sign = _reduce_angle(x, r, reduce=certain_x_in_range != 90)

    temp0 = _double(3)
    r.value *= r
    temp0.value = 32400.0
    temp0.value += r
    assign_to.value = 32400.0 if sign == 1 else -32400.0
    r.value *= 4.0
    if sign == 1:
        assign_to.value -= r
    else:
        assign_to.value += r
    assign_to.value /= temp0
    if fold_sign is not None:
        assign_to.value *= fold_sign


def approximate_tan(
    x: Checkable,
    *,
    assign_to: Editable,
    can_modify_x: bool = False,
    certain_x_in_range: Literal[90] | None = None,
) -> None:
    """tan(x degrees) as one direct rational whose denominator carries the
    +-90 poles (coefficients by VariousCacti; max relative error ~6e-4).
    tan has period 180, so the fold needs no parity sign - 21 actions, no
    conditionals, against 33 for the sin/cos ratio. At exactly +-90 the
    denominator is 0 and the division no-ops, leaving a bounded value.
    """
    x = x.as_double()
    r = _reduction_input(x, can_modify_x)
    _reduce_angle(
        x,
        r,
        reduce=certain_x_in_range != 90,
        with_parity=False,
    )

    r2 = _double(2)
    den = _double(3)
    r2.value = r
    r2.value *= r
    assign_to.value = r2
    assign_to.value *= 1.59250708302
    assign_to.value += -54211.9648185
    assign_to.value *= r
    den.value = 8100.0
    den.value -= r2
    assign_to.value /= den
    r2.value *= 0.0028598955042
    r2.value += -383.471207804
    assign_to.value /= r2


# Degree-5 odd minimax fit of atan on [-1, 1], in degrees: even powers only,
# so the octant fold needs no absolute values. Max error 0.036 degrees.
_ATAN_C0 = 57.02986
_ATAN_C1 = -16.54148
_ATAN_C2 = 4.54673


def approximate_atan2(
    y: Checkable | float | int,
    x: Checkable | float | int,
    *,
    assign_to: Editable,
    assume_x_non_negative: bool = False,
) -> None:
    """atan2(y, x) in degrees, in (-180, 180]: the full-quadrant inverse
    tangent, e.g. the yaw that would face from one point toward another.

    Conditional-free: the octant fold, the sign of y and the left-half-plane
    correction all come from the truncating-cast step gadget, so the whole
    thing is straight-line arithmetic (~56 actions; fewer when an operand is
    a literal or `assume_x_non_negative` skips the correction). Requires
    |x|, |y| <= 30,000 (the gadget's bound on x^2 - y^2). atan2(0, 0) is 0
    and the axes resolve exactly; the polynomial is within 0.04 degrees.
    """
    if isinstance(y, int | float) and isinstance(x, int | float):
        assign_to.value = math.degrees(math.atan2(float(y), float(x)))
        return
    for operand in (y, x):
        if isinstance(operand, Checkable) and operand.equals(assign_to):
            raise ValueError('Cannot assign to the same stat as an input')

    x2 = _double(0)
    y2 = _double(1)
    fold = _double(2)
    flip = _double(3)
    num = _double(4)
    den = _double(5)
    sign_y = _double(6)

    def squared(slot: Editable, value: Checkable | float | int) -> Checkable | float:
        if isinstance(value, int | float):
            return float(value) * float(value)
        slot.value = value
        slot.value *= value
        return slot

    x_squared = squared(x2, x)
    y_squared = squared(y2, y)

    # fold <- +1 if |x| >= |y| else -1; it doubles as the polynomial's sign
    # factor (-atan(x/y) in the flipped octants).
    fold.value = x_squared
    fold.value -= y_squared
    _sign_into(fold, fold)
    # flip in {0, 1}
    flip.value = fold
    flip.value *= -0.5
    flip.value += 0.5

    # z = (the smaller-magnitude leg) / (the larger): blend with flip. Both
    # blends are 0 at x = y = 0, so the division no-ops onto num = 0 there.
    num.value = x
    num.value -= y
    num.value *= flip
    num.value += y
    den.value = y
    den.value -= x
    den.value *= flip
    den.value += x
    num.value /= den

    den.value = num
    den.value *= num
    assign_to.value = _ATAN_C2
    assign_to.value *= den
    assign_to.value += _ATAN_C1
    assign_to.value *= den
    assign_to.value += _ATAN_C0
    assign_to.value *= num
    assign_to.value *= fold

    if isinstance(y, int | float):
        y_negative = float(y) < 0
        flip.value *= -90.0 if y_negative else 90.0
        assign_to.value += flip
    else:
        _sign_into(sign_y, y)
        flip.value *= 90.0
        flip.value *= sign_y
        assign_to.value += flip

    if isinstance(x, Checkable) and not assume_x_non_negative:
        # += 180 * sign(y) when x < 0 and the fold was direct (fold == +1
        # there can only happen with |x| >= |y|... the correction applies to
        # the unflipped octants, i.e. (1 + fold) / 2).
        half = _step_non_negative(x2, x)
        half.value -= 1
        x2.cast_to_double()
        num.value = fold
        num.value += 1.0
        num.value *= -90.0
        x2.value *= num
        if isinstance(y, int | float):
            if float(y) < 0:
                x2.value *= -1.0
        else:
            x2.value *= sign_y
        assign_to.value += x2


def approximate_atan(
    x: Checkable | float | int,
    *,
    assign_to: Editable,
) -> None:
    """atan(x) in degrees, in (-90, 90): conditional-free via atan2(x, 1)."""
    approximate_atan2(x, 1.0, assign_to=assign_to)


def approximate_asin(
    x: Checkable,
    *,
    assign_to: Editable,
) -> None:
    """asin(x) in degrees for x in [-1, 1], as atan2(x, sqrt(1 - x^2)).

    Costs a full approximate_sqrt, so it is the most expensive of the
    inverse family; near +-1 the sqrt's error steepens the result.
    """
    if x.equals(assign_to):
        raise ValueError('Cannot assign to the same stat as input')
    inner = _double(_CARRY)
    cosine = _double(_CARRY + 1)
    inner.value = x
    inner.value *= x
    inner.value *= -1.0
    inner.value += 1.0
    approximate_sqrt(inner, assign_to=cosine, can_modify_x=True)
    approximate_atan2(x, cosine, assign_to=assign_to, assume_x_non_negative=True)


def approximate_acos(
    x: Checkable,
    *,
    assign_to: Editable,
) -> None:
    """acos(x) in degrees for x in [-1, 1], as 90 - asin(x)."""
    approximate_asin(x, assign_to=assign_to)
    assign_to.value *= -1.0
    assign_to.value += 90.0


# Degree-3 minimax fit of 2^f on [0, 1); max relative error ~1.1e-4, below
# the placeholder round-trip's own noise.
_EXP2_C0 = 0.9998924509382545
_EXP2_C1 = 0.696460057613672
_EXP2_C2 = 0.2243359708282287
_EXP2_C3 = 0.07920396862261869

_LOG2_E = 1.4426950408889634
_LN_2 = 0.6931471805599453

# Degree-4 minimax fit of ln(m) on [1, 2]; max error ~6.1e-5.
_LN_C0 = -1.7417507258348537
_LN_C1 = 2.821106417137134
_LN_C2 = -1.4698838732605717
_LN_C3 = 0.44715847297414424
_LN_C4 = -0.05656926491710523


def approximate_exp(
    x: Checkable | float | int,
    *,
    assign_to: Editable,
) -> None:
    """e^x for x in [-22, 21]: split x*log2(e) into an integer power of two
    (one variable-distance shift, offset by 32 so negative exponents need no
    branch) and a cubic on the fractional part. 20 actions, no conditionals;
    relative error ~2e-4.
    """
    if isinstance(x, int | float):
        assign_to.value = math.exp(float(x))
        return
    frac = _double(0)
    whole = _double(1)
    power = _scratch(2).as_long()

    frac.value = x
    frac.value *= _LOG2_E
    whole.value = frac
    whole.value += 32.0
    whole.cast_to_long()
    power.value = 1
    power.value <<= whole.as_long()
    power.cast_to_double()
    whole.cast_to_double()
    frac.value -= whole
    frac.value += 32.0

    assign_to.value = _EXP2_C3
    assign_to.value *= frac
    assign_to.value += _EXP2_C2
    assign_to.value *= frac
    assign_to.value += _EXP2_C1
    assign_to.value *= frac
    assign_to.value += _EXP2_C0
    assign_to.value *= power.as_double()
    assign_to.value /= 4294967296.0


# Bisect levels for the exponent extraction, on x' = x * 2^20 < 2^51.
_LN_LEVELS = (32, 16, 8, 4, 2, 1)
_LN_OFFSET = 1 << 51


def approximate_ln(
    x: Checkable,
    *,
    assign_to: Editable,
) -> None:
    """ln(x) for x in (0.001, 1e9]: extract floor(log2) with a
    conditional-free six-level bisect (each level is one step gadget, one
    variable-distance shift and one division), then a quartic on the
    mantissa. ~76 actions, no conditionals; error ~5e-4. The lower bound is
    the placeholder's own readability floor: a smaller x rounds to 0.0000 in
    the first read.
    """
    if x.equals(assign_to):
        raise ValueError('Cannot assign to the same stat as input')
    mantissa = _double(0)
    gate = _double(1)
    divisor = _scratch(2).as_long()
    exponent = _scratch(3).as_long()

    # Pre-scale by 2^20 so sub-1 inputs keep a non-negative exponent.
    mantissa.value = x
    mantissa.value *= 1048576.0
    exponent.value = 0
    for level in _LN_LEVELS:
        # The step gadget with a wider offset: the mantissa runs to 2^51.
        gate.value = mantissa
        gate.value += float(_LN_OFFSET - (1 << level))
        gate.cast_to_long()
        gate_long = gate.as_long()
        gate_long.value //= _LN_OFFSET
        gate_long.value *= level
        exponent.value += gate_long
        divisor.value = 1
        divisor.value <<= gate_long
        divisor.cast_to_double()
        mantissa.value /= divisor.as_double()

    assign_to.value = _LN_C4
    assign_to.value *= mantissa
    assign_to.value += _LN_C3
    assign_to.value *= mantissa
    assign_to.value += _LN_C2
    assign_to.value *= mantissa
    assign_to.value += _LN_C1
    assign_to.value *= mantissa
    assign_to.value += _LN_C0
    exponent.cast_to_double()
    gate.value = exponent.as_double()
    gate.value *= _LN_2
    assign_to.value += gate
    assign_to.value -= 20.0 * _LN_2


def approximate_log10(
    x: Checkable,
    *,
    assign_to: Editable,
) -> None:
    """log10(x) for x in (1e-6, 1e9]: ln(x) / ln(10)."""
    approximate_ln(x, assign_to=assign_to)
    assign_to.value *= 0.4342944819032518


def approximate_pow(
    base: Checkable,
    exponent: Checkable | float | int,
    *,
    assign_to: Editable,
) -> None:
    """base^exponent.

    A literal integer exponent (|n| <= 64) compiles to a square-and-multiply
    chain - a handful of multiplies, any base. Otherwise base must be
    positive and the result is exp(exponent * ln(base)), inheriting both
    domains (base in (0.001, 1e9], |exponent * ln(base)| <= 21).
    """
    if base.equals(assign_to) or (
        isinstance(exponent, Checkable) and exponent.equals(assign_to)
    ):
        raise ValueError('Cannot assign to the same stat as an input')

    if isinstance(exponent, int) and abs(exponent) <= 64:
        n = abs(exponent)
        if n == 0:
            assign_to.value = 1.0
            return
        square = _double(_CARRY)
        square.value = base
        assign_to.value = base if n % 2 else 1.0
        n //= 2
        while n:
            square.value *= square
            if n % 2:
                assign_to.value *= square
            n //= 2
        if exponent < 0:
            square.value = 1.0
            square.value /= assign_to
            assign_to.value = square
        return

    log = _double(_CARRY)
    approximate_ln(base, assign_to=log)
    log.value *= exponent
    approximate_exp(log, assign_to=assign_to)


def approximate_hypot(
    x: Checkable,
    y: Checkable,
    z: Checkable | None = None,
    *,
    assign_to: Editable,
) -> None:
    """sqrt(x^2 + y^2 [+ z^2]) - the straight-line distance."""
    acc = _double(_CARRY)
    term = _double(_CARRY + 1)
    acc.value = x
    acc.value *= x
    term.value = y
    term.value *= y
    acc.value += term
    if z is not None:
        term.value = z
        term.value *= z
        acc.value += term
    approximate_sqrt(acc, assign_to=assign_to, can_modify_x=True)
