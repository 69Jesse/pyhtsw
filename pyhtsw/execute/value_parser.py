import re
from typing import TYPE_CHECKING

import numpy as np

from .backend_type import BackendType, JavaLong, backend_into_string
from .java_long import INT64_MAX, INT64_MIN

if TYPE_CHECKING:
    from .context import ExecutionContext
    from .player import ExecutionPlayer

__all__ = (
    'parse_string',
    'parse_value',
)


PLACEHOLDER_REGEX = re.compile(r'%([^%]+?)%')
# htsw's EXPLICIT_DOUBLE_REGEX has no sign support, which would make every
# D-cast (and every double-typed copy) of a fractional negative value corrupt
# to a string — while its long path does accept a minus. The asymmetry looks
# like an htsw oversight rather than Housing behavior, so this port accepts a
# leading minus. Not yet verified in-game; if Housing really rejects negative
# doubles here, `cast_to_double` and friends have a live bug.
EXPLICIT_DOUBLE_REGEX = re.compile(r'^-?(0|[1-9]\d*)(\.\d+)$')
BARE_LONG_REGEX = re.compile(r'-?\d+')


class InvalidValueError(ValueError):
    pass


def _is_long_string(value: str) -> bool:
    if BARE_LONG_REGEX.fullmatch(value) is None:
        return False
    number = int(value)
    if number < INT64_MIN or number > INT64_MAX:
        return False
    return str(number) == value


def _parse_long_saturating(value: str) -> JavaLong:
    number = int(value)
    if INT64_MIN <= number <= INT64_MAX:
        return JavaLong(number)
    return JavaLong(INT64_MAX if value.startswith('-') else INT64_MIN)


def _render_var(value: BackendType) -> str:
    if isinstance(value, np.floating):
        fixed = f'{float(value):.4f}'
        whole, dec = fixed.split('.')
        negative = whole.startswith('-')
        digits = whole[1:] if negative else whole
        rounded = (int((dec + '0000')[:4]) + 5) // 10
        carried = rounded >= 1000
        if carried:
            # .9995 and up round into the whole part.
            rounded -= 1000
            digits = str(int(digits) + 1)
        display = str(rounded).rjust(3, '0').rstrip('0')
        if not display and not carried:
            display = dec.rstrip('0')
        if not display:
            display = '0'
        grouped = format(int(digits), ',')
        if negative:
            grouped = '-' + grouped
        return f'{grouped}.{display}'
    return backend_into_string(value)


def _run_placeholder(
    context: 'ExecutionContext',
    content: str,
    *,
    player: 'ExecutionPlayer | None',
) -> BackendType | None:
    from ..checkable import Checkable
    from ..stats.global_stat import GlobalStat
    from ..stats.player_stat import PlayerStat
    from ..stats.team_stat import TeamStat

    trimmed = content.strip()
    slash = trimmed.find('/')
    if slash >= 0:
        kind = trimmed[:slash]
        args_string = trimmed[slash + 1 :]
        args = [arg for arg in args_string.split(' ') if arg] if args_string else []
        if args_string and not args:
            args = ['']
    else:
        parts = trimmed.split(' ')
        kind, args = parts[0], parts[1:]

    def resolve_var(stat: object, fallback_raw: str | None) -> BackendType:
        raw = context._get_raw(stat, player=player)  # type: ignore[arg-type]
        if raw is not None:
            return raw
        return parse_value(
            context,
            fallback_raw if fallback_raw is not None else '""',
            player=player,
        )

    def resolve_stat(stat: object) -> BackendType:
        raw = context._get_raw(stat, player=player)  # type: ignore[arg-type]
        if isinstance(raw, JavaLong):
            return raw
        return JavaLong(0)

    if kind == 'var.player':
        return resolve_var(
            PlayerStat(args[0] if args else ''),
            args[1] if len(args) > 1 else None,
        )
    if kind == 'var.global':
        return resolve_var(
            GlobalStat(args[0] if args else ''),
            args[1] if len(args) > 1 else None,
        )
    if kind == 'var.team':
        key = args[0] if args else ''
        team = args[1] if len(args) > 1 else ''
        return resolve_var(TeamStat(key, team), args[2] if len(args) > 2 else None)
    if kind == 'stat.player':
        return resolve_stat(PlayerStat(args[0] if args else ''))
    if kind == 'stat.global':
        return resolve_stat(GlobalStat(args[0] if args else ''))
    if kind == 'stat.team':
        key = args[0] if args else ''
        team = args[1] if len(args) > 1 else ''
        return resolve_stat(TeamStat(key, team))

    # Any other placeholder type falls back to the simulator's registered
    # placeholder classes (dates, player values, ...), mirroring htsw's other
    # placeholder behaviors.
    text = f'%{content}%'
    for pattern, factory in Checkable.iter_pattern_factories():
        match = pattern.fullmatch(text)
        if match is None:
            continue
        return context._get_raw(factory(match), default='', player=player)
    return None


def parse_string(
    context: 'ExecutionContext',
    value: str,
    *,
    player: 'ExecutionPlayer | None' = None,
) -> BackendType:
    """htsw `parseString`: one interpolation pass, then number typing."""
    placeholders = PLACEHOLDER_REGEX.findall(value)

    if not placeholders:
        return value

    replaced = value
    for content in placeholders:
        placeholder = f'%{content}%'
        try:
            resolved = _run_placeholder(context, content, player=player)
            if resolved is None:
                raise InvalidValueError('Unresolved placeholder')
            replaced = replaced.replace(placeholder, _render_var(resolved), 1)
        except Exception:  # noqa: BLE001 - htsw ignores per-placeholder errors
            pass

    # The replaced value is only used if it is not too long.
    if len(replaced) <= 32:
        value = replaced

    if _is_long_string(value):
        return _parse_long_saturating(value)
    if EXPLICIT_DOUBLE_REGEX.fullmatch(value) is not None:
        return np.float64(value)

    last_char = value[-1:].upper()
    if last_char not in ('L', 'D'):
        return value

    base_value = value[:-1].replace(',', '')
    if _is_long_string(base_value) or EXPLICIT_DOUBLE_REGEX.fullmatch(base_value):
        if last_char == 'L':
            return _parse_long_saturating(base_value.split('.')[0])
        return np.float64(base_value)

    return value


def parse_value(
    context: 'ExecutionContext',
    value: str,
    *,
    player: 'ExecutionPlayer | None' = None,
) -> BackendType:
    """htsw `parseValue`: how a CHANGE_VAR right-hand side resolves."""
    if not value:
        raise InvalidValueError('Input value cannot be null or empty.')

    if value.startswith('%') and value.endswith('%') and len(value) > 2:
        content = value[1:-1]
        resolved = _run_placeholder(context, content, player=player)
        if resolved is None:
            # htsw warns and yields long zero for an unresolvable placeholder.
            return JavaLong(0)
        if isinstance(resolved, str):
            return parse_string(context, resolved, player=player)
        return resolved

    if value.startswith('"') and value.endswith('"'):
        return parse_string(context, value[1:-1], player=player)

    if '.' in value:
        try:
            return np.float64(value)
        except ValueError:
            pass

    if BARE_LONG_REGEX.fullmatch(value) is not None:
        return _parse_long_saturating(value)

    raise InvalidValueError('Invalid value')
