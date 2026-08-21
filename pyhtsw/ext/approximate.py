import math
from typing import Literal, overload

from ..actions.conditional.statements import Else, IfAll
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
    'approximate_sin',
    'approximate_sin_cos',
    'approximate_sqrt',
    'approximate_tan',
)


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

    temp0 = TemporaryStat().as_double()
    temp1 = TemporaryStat().as_double()
    temp2 = TemporaryStat().as_double()
    temp3 = TemporaryStat().as_double()
    if not can_modify_x:
        x_or_temp4 = TemporaryStat().as_double()
    else:
        assert isinstance(x, Editable)
        x_or_temp4 = x.as_double()
        if isinstance(x_or_temp4, Stat):
            x_or_temp4 = x_or_temp4.without_auto_unset()

    assign_to = assign_to.as_double()

    # The old fixed-point scale (SQRT_INV_SCALAR = 1000) was a no-op: the
    # descaled iteration is identical to 8 significant digits across the whole
    # domain, simulator rounding included, so its three normalization divides
    # were pure cost.
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
        return TemporaryStat().as_double()
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
) -> TemporaryStat | None:
    if not reduce:
        reduced.value = x
        return None
    fold = TemporaryStat().as_double()
    fold_sign = TemporaryStat().as_double()
    reduced.value = x
    reduced.value += 36090.0
    fold.value = reduced
    fold.value /= 180.0
    fold.cast_to_long()
    fold.cast_to_double()
    # fold_sign = 1 - 2 * (fold mod 2): +1 on even folds, -1 on odd.
    fold_sign.value = fold
    fold_sign.value /= 2.0
    fold_sign.cast_to_long()
    fold_sign.cast_to_double()
    fold_sign.value *= 2.0
    fold_sign.value -= fold
    fold_sign.value *= 2.0
    fold_sign.value += 1.0
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
    """
    Approximate sine and cosine at the same time, AMAZINGLY BLAZINGLY EPIC GAMERLY fast

    Assumes x is in degrees,
    if you're certain x is in the range of [-90, 90] or [-180, 180],
    you may set certain_x_in_range to 90 or 180 respectively.
    """

    x = x.as_double()
    temp0 = TemporaryStat().as_double()
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
    """sin(x degrees) alone: 7 actions past the shared range reduction,
    against the pair's 12."""
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
    """cos(x degrees) alone: 6 actions past the shared range reduction."""
    x = x.as_double()
    r = _reduction_input(x, can_modify_x)
    fold_sign = _reduce_angle(x, r, reduce=certain_x_in_range != 90)

    temp0 = TemporaryStat().as_double()
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
    certain_x_in_range: Literal[90, 180] | None = None,
) -> None:
    """tan(x degrees) as the sin/cos ratio of the shared approximation.

    At exactly +-90 the cosine approximation is 0 and the division no-ops,
    leaving the sine's +-1 in the output - bounded rather than infinite.
    Accuracy degrades within a few degrees of the poles, where the small
    cosine amplifies the pair's error.
    """
    sin = TemporaryStat().as_double()
    cos = TemporaryStat().as_double()
    approximate_sin_cos(
        x,
        assign_to_sin=sin,
        assign_to_cos=cos,
        can_modify_x=can_modify_x,  # type: ignore[arg-type]
        certain_x_in_range=certain_x_in_range,
    )
    assign_to.value = sin
    assign_to.value /= cos


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

    Three conditionals (two if `x` is a non-negative literal or
    `assume_x_non_negative` is set): the octant fold, the sign of y, and the
    left-half-plane correction; everything else is arithmetic. atan2(0, 0)
    is 0, the axes resolve exactly (+-90, 180), and the polynomial is within
    0.04 degrees.
    """
    if isinstance(y, int | float) and isinstance(x, int | float):
        assign_to.value = math.degrees(math.atan2(float(y), float(x)))
        return
    for operand in (y, x):
        if isinstance(operand, Checkable) and operand.equals(assign_to):
            raise ValueError('Cannot assign to the same stat as an input')

    def squared(value: Checkable | float | int) -> Checkable | float:
        if isinstance(value, int | float):
            return float(value) * float(value)
        stat = TemporaryStat().as_double()
        stat.value = value
        stat.value *= value
        return stat

    y2 = squared(y)
    x2 = squared(x)
    z = TemporaryStat().as_double()
    mul = TemporaryStat().as_double()
    off = TemporaryStat().as_double()
    scratch = TemporaryStat().as_double()

    # Preseed so the x = y = 0 edge (both divides no-op) lands on 0.
    z.value = 0.0
    with IfAll(y2 > x2):
        z.value = x
        z.value /= y
        mul.value = -1.0
        off.value = 90.0
    with Else:
        z.value = y
        z.value /= x
        mul.value = 1.0
        off.value = 0.0

    scratch.value = z
    scratch.value *= z
    assign_to.value = _ATAN_C2
    assign_to.value *= scratch
    assign_to.value += _ATAN_C1
    assign_to.value *= scratch
    assign_to.value += _ATAN_C0
    assign_to.value *= z
    assign_to.value *= mul

    if isinstance(y, int | float):
        if y < 0:
            assign_to.value -= off
        else:
            assign_to.value += off
        y_negative = float(y) < 0
        if isinstance(x, Checkable) and not assume_x_non_negative:
            with IfAll(mul == 1.0, x < 0.0):
                assign_to.value += -180.0 if y_negative else 180.0
        return

    sign_y = TemporaryStat().as_double()
    sign_y.value = 1.0
    with IfAll(y < 0.0):
        sign_y.value = -1.0
    off.value *= sign_y
    assign_to.value += off
    if isinstance(x, Checkable) and not assume_x_non_negative:
        scratch.value = sign_y
        scratch.value *= 180.0
        with IfAll(mul == 1.0, x < 0.0):
            assign_to.value += scratch


def approximate_atan(
    x: Checkable | float | int,
    *,
    assign_to: Editable,
) -> None:
    """atan(x) in degrees, in (-90, 90): two conditionals via atan2(x, 1)."""
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
    inner = TemporaryStat().as_double()
    cosine = TemporaryStat().as_double()
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
