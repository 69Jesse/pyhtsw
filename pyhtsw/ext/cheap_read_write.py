import math
from collections.abc import Iterable, Sequence
from typing import Any, NamedTuple

from ..actions.conditional.statements import Else, IfAll, IfAny
from ..editable import Checkable, Editable, HousingType
from ..internal_type import InternalType
from ..stats.global_stat import GlobalStat
from ..stats.player_stat import PlayerStat
from ..stats.stat import Stat
from .set_string import set_string

__all__ = (
    'cheap_read',
    'cheap_write',
)


def assign(
    dst: Sequence[Editable],
    src: Sequence[Checkable | HousingType],
) -> None:
    for d, s in zip(dst, src, strict=True):
        d.value = s


def make_temps(
    i: int,
    template: Sequence[Checkable | HousingType],
) -> tuple[PlayerStat, ...]:
    width = len(template)
    return tuple(
        PlayerStat(f'tmp{i * width + k}').as_type(InternalType.from_value(template[k]))
        for k in range(width)
    )


def assert_same_widths(items: Iterable[Sequence[Any]]) -> int:
    width = len(next(iter(items), ()))
    for item in items:
        if len(item) != width:
            raise ValueError('All items must have the same width')
    return width


def _common_prefix(names: Sequence[str]) -> str:
    if not names:
        return ''
    p = names[0]
    for n in names[1:]:
        i = 0
        while i < len(p) and i < len(n) and p[i] == n[i]:
            i += 1
        p = p[:i]
        if not p:
            break
    return p


def _common_suffix(names: Sequence[str]) -> str:
    if not names:
        return ''
    s = names[0]
    for n in names[1:]:
        i = 0
        while i < len(s) and i < len(n) and s[-1 - i] == n[-1 - i]:
            i += 1
        s = s[len(s) - i :] if i else ''
        if not s:
            break
    return s


def _parse_comma_int(text: str) -> int | None:
    if not text:
        return None
    raw = text.replace(',', '')
    if not raw.isdigit():
        return None
    n = int(raw)
    if format(n, ',') != text:
        return None
    return n


def _detect_linear_run(
    names: Sequence[str],
    expected_step: int,
) -> tuple[str, str, int] | None:
    if len(names) < 2:
        return None
    prefix = _common_prefix(names)
    suffix = _common_suffix(names)
    if '%' in prefix or '%' in suffix or '"' in prefix or '"' in suffix:
        return None
    suffix_len = len(suffix)
    middles: list[str] = []
    for name in names:
        if len(prefix) + suffix_len > len(name):
            return None
        middle = (
            name[len(prefix) : len(name) - suffix_len]
            if suffix_len
            else name[len(prefix) :]
        )
        middles.append(middle)
    start = _parse_comma_int(middles[0])
    if start is None:
        return None
    for i, mid in enumerate(middles):
        if mid != format(start + expected_step * i, ','):
            return None
    return prefix, suffix, start


# (stat_class, prefix, suffix, coeff, offset)
type ColumnInfo = tuple[type[Stat], str, str, int, int]


def _uniform_stat_class(stats: Sequence[Any]) -> type[Stat] | None:
    if not stats:
        return None
    cls = type(stats[0])
    if cls is not PlayerStat and cls is not GlobalStat:
        return None
    for s in stats[1:]:
        if type(s) is not cls:
            return None
    return cls


def _detect_pattern_a(
    items: Sequence[Sequence[Checkable | HousingType]],
) -> list[ColumnInfo] | None:
    width = len(items[0])
    flat = [items[i][k] for i in range(len(items)) for k in range(width)]
    cls = _uniform_stat_class(flat)
    if cls is None:
        return None
    info = _detect_linear_run(
        [s.name for s in flat if isinstance(s, Stat)],
        expected_step=1,
    )
    if info is None:
        return None
    prefix, suffix, start = info
    return [(cls, prefix, suffix, width, start + k) for k in range(width)]


def _detect_pattern_b(
    items: Sequence[Sequence[Checkable | HousingType]],
) -> list[ColumnInfo] | None:
    width = len(items[0])
    results: list[ColumnInfo] = []
    for k in range(width):
        column = [items[i][k] for i in range(len(items))]
        cls = _uniform_stat_class(column)
        if cls is None:
            return None
        info = _detect_linear_run(
            [s.name for s in column if isinstance(s, Stat)],
            expected_step=1,
        )
        if info is None:
            return None
        prefix, suffix, start = info
        results.append((cls, prefix, suffix, 1, start))
    return results


def _detect_pattern(
    items: Sequence[Sequence[Checkable | HousingType]],
) -> list[ColumnInfo] | None:
    if len(items) < 2:
        return None
    return _detect_pattern_a(items) or _detect_pattern_b(items)


_FAST_READ_NAMES = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'


def _fast_names_pool(pattern: list[ColumnInfo]) -> str:
    excluded = {
        prefix
        for cls, prefix, _suffix, _coeff, _offset in pattern
        if cls is PlayerStat and len(prefix) == 1
    }
    return ''.join(c for c in _FAST_READ_NAMES if c not in excluded)


def _emit_fast_read(
    *,
    pattern: list[ColumnInfo],
    index: Editable,
    output: Sequence[Editable],
) -> None:
    width = len(pattern)
    names = _fast_names_pool(pattern)
    if 3 * width > len(names):
        raise ValueError(f'cheap_read fast path: width {width} too large')
    # The index is interpolated into a name, so it has to survive as a literal
    # `0`: with auto-unset on, a zero index removes the stat and the placeholder
    # resolves to nothing, leaving the prefix on its own as the name.
    n_stats = [
        PlayerStat(names[k]).as_long().without_auto_unset() for k in range(width)
    ]
    tmp_str_stats = [PlayerStat(names[width + k]) for k in range(width)]
    p_stats = [PlayerStat(names[2 * width + k]) for k in range(width)]

    for k, (cls, prefix, suffix, coeff, offset) in enumerate(pattern):
        scope = cls.right_side_keyword()
        n_k = n_stats[k]
        tmp_str_k = tmp_str_stats[k]

        if coeff == 1:
            n_k.value = index if offset == 0 else index + offset
        else:
            n_k.value = index * coeff if offset == 0 else index * coeff + offset

        # The scope head always rides in the prefix variable — even when the
        # item names have no shared prefix. A literal `%var.player/` written
        # inline would pair its `%` with the counter's and be eaten.
        p_k = p_stats[k]
        p_k.value = f'%var.{scope}/{prefix}'
        template = f'%var.player/{p_k.name}%%var.player/{n_k.name}%{suffix}%'

        set_string(tmp_str_k, template)
        tmp_str_k.set(tmp_str_k, is_intentional_self_assignment=True)
        output[k].value = tmp_str_k


type MaybeSequence[T] = T | Sequence[T]


def into_sequence[T](item: MaybeSequence[T]) -> Sequence[T]:
    return item if isinstance(item, Sequence) else (item,)


# Housing's per-action-list caps; a conditional's branch gets its own budget.
_BE_LIMIT = 25

_HI_KEY = 500
# Band gates compute `1 - min(1, (h - a)^2)` via `//`; the divisor bounds the
# square, so |h - a| up to 2^26 stays exact and overflow-free.
_BAND_DIV = 1 << 53


def _in_nested_container() -> bool:
    from ..container import get_current_container

    return any(
        ctx.parent_expression is not None for ctx in get_current_container().contexts
    )


class _FastWriteShape(NamedTuple):
    chunk: int
    chunks: int
    table: int
    split: bool
    mid: int
    pairs: int
    lone: int
    flip_ok: bool
    payloads_per_column: int


def _fast_write_shape(n: int, width: int, chunk: int) -> _FastWriteShape:
    chunks = math.ceil(n / chunk)
    table = min(chunk, n)
    split = table * width + (table - 1) > _BE_LIMIT
    mid = (table + 1) // 2
    pairs = chunks // 2 if chunks >= 3 else 0
    lone = chunks % 2 if chunks >= 3 else 0
    return _FastWriteShape(
        chunk=chunk,
        chunks=chunks,
        table=table,
        split=split,
        mid=mid,
        pairs=pairs,
        lone=lone,
        flip_ok=chunks <= 4,
        payloads_per_column=2 if split else 1,
    )


def _fast_write_costs(n: int, width: int, chunk: int) -> tuple[int, int]:
    s = _fast_write_shape(n, width, chunk)
    npay = s.payloads_per_column * width
    scatter = s.table * width + (s.table - 1)

    setup = 5 * width + 2 * width + width + 1  # read, diff, prefixes, counter
    if s.chunks >= 2:
        setup += 4  # counter -> index mod chunk
    if s.split:
        setup += 3 * width + 2  # payload split
    if s.chunks >= 3:
        setup += 2  # h = index // (2 * chunk)
        if s.pairs >= 2:
            setup += npay  # stashes
        if not s.lone:
            setup += npay + (3 if s.pairs > 2 else 0)  # first pair's kill
    if not s.split:
        setup += scatter
    if s.chunks == 1 and not s.split:
        setup += n * width  # inline blits

    def gate(a: int) -> int:
        if s.flip_ok:
            return 2
        return 6 if a == 0 else 7

    runs = [setup]
    if s.chunks == 1 and s.split:
        runs.append(n * width)  # blits after the scatter conditional
    if s.lone:
        runs.append(gate(s.pairs - 1) + npay)
    for a in range(s.pairs - 1, 0, -1):
        runs.append(npay + gate(a - 1) + npay)

    budget = _BE_LIMIT
    wrappers = 0
    for run in runs:
        if run <= budget:
            budget -= run
        else:
            wrappers += math.ceil(run / _BE_LIMIT)

    conditionals = wrappers + (1 if s.split else 0)
    if s.chunks == 2:
        conditionals += 1
    elif s.chunks >= 3:
        conditionals += s.lone + s.pairs

    expressions = sum(runs)
    if s.split:
        expressions += scatter + 1  # the high branch's counter offset
    if s.chunks >= 2:
        expressions += n * width
    return conditionals, expressions


def _emit_fast_write(
    *,
    pattern: list[ColumnInfo],
    items: Sequence[Sequence[Editable]],
    index: Editable,
    input: Sequence[Checkable | HousingType],
    chunk: int,
) -> None:
    from ..actions.preserved import preserved
    from ..actions.strict_order import strict_order
    from ..stats.temporary_stat import TemporaryStat

    n = len(items)
    width = len(pattern)
    s = _fast_write_shape(n, width, chunk)

    pool = _fast_names_pool(pattern)
    if 4 * width + 1 > len(pool):
        raise ValueError(f'cheap_write fast path: width {width} too large')
    # `_emit_fast_read` claims pool[:3 * width] for itself.
    q_stats = [PlayerStat(pool[3 * width + k]) for k in range(width)]
    d = PlayerStat(pool[4 * width]).as_long().without_auto_unset()
    lo = [PlayerStat(f'hw{k}_0').as_long() for k in range(width)]
    hi = [PlayerStat(f'hw{k}_{_HI_KEY}').as_long() for k in range(width)]
    payloads = lo + hi if s.split else lo
    # The un-rebaked part of the table may be unset (first call), so a blit
    # needs the explicit 0 fallback: an empty-string resolve is fatal in-game.
    slots = [
        [PlayerStat(f'sw{j}_{k}', fallback_value=0) for k in range(width)]
        for j in range(s.table)
    ]
    t = TemporaryStat().as_long()
    h = TemporaryStat().as_long()
    band = TemporaryStat().as_long()
    stashes = [TemporaryStat().as_long() for _ in payloads]

    def bake(j: int) -> None:
        for k in range(width):
            # Exactly 32 characters, the most one assignment holds. The
            # trailing `L` rides along unresolved and lands on the number the
            # one-hot yields, which is what lets the blit read it back: that
            # number is rendered with thousands separators, and only the `...L`
            # form strips them before parsing.
            set_string(
                slots[j][k],
                f'%var.player/{q_stats[k].name}%%var.player/{d.name}% 0%L',
            )

    def blit(chunk_idx: int) -> None:
        start = chunk_idx * chunk
        for j, item in enumerate(items[start : start + chunk]):
            for k in range(width):
                # A slot holds the *unresolved* one-hot reference, so the blit
                # has to resolve twice. Only a bare `%...%` right-hand side does
                # that; the quoted form a typed left side would coerce it into
                # stops after one pass and yields the text. Widening the left
                # side to ANY suppresses that coercion.
                item[k].as_type(InternalType.ANY).value += slots[j][k]

    def gate_flag(a: int) -> Stat:
        """1 if h == a else 0. The flip shortcut needs h in {0, 1}, which
        holds for in-range indices whenever there are at most two bands."""
        if s.flip_ok:
            assert a == 0
            h.value *= -1
            h.value += 1
            return h
        band.value = h
        if a != 0:
            band.value -= a
        band.value *= band
        band.value += _BAND_DIV - 1
        band.value //= _BAND_DIV
        band.value *= -1
        band.value += 1
        return band

    def kill(flag: Stat) -> None:
        for payload in payloads:
            payload.value *= flag

    with strict_order(), preserved():
        # lo_k = diff_k = input[k] - items[index][k], via one composed read.
        _emit_fast_read(pattern=pattern, index=index, output=lo)
        for k in range(width):
            lo[k].value *= -1
            lo[k].value += input[k]
        d.value = index
        if s.chunks >= 2:
            # d -> p = index mod chunk.
            d.value //= chunk
            d.value *= chunk
            d.value -= index
            d.value *= -1
        if s.split:
            # Route the diff to the rebaked half's payload key.
            t.value = d
            t.value //= s.mid
            for k in range(width):
                hi[k].value = lo[k]
                hi[k].value *= t
                lo[k].value -= hi[k]
        for k in range(width):
            q_stats[k].value = f'%var.player/hw{k}_'
        if s.chunks >= 3:
            h.value = index
            h.value //= 2 * chunk
            if s.pairs >= 2:
                for stash, payload in zip(stashes, payloads, strict=True):
                    stash.value = payload
            if not s.lone:
                # The first gather pair is the top band: kill unless it.
                if s.pairs == 2:
                    kill(h)
                else:
                    band.value = h
                    band.value += 1
                    band.value //= s.pairs
                    kill(band)

        if s.split:
            # Rebake only the half of the table containing p.
            with IfAll(d <= s.mid - 1):
                for j in range(s.mid):
                    bake(j)
                    if j != s.mid - 1:
                        d.value -= 1
            with Else:
                d.value += _HI_KEY - s.mid
                for j in range(s.mid, s.table):
                    bake(j)
                    if j != s.table - 1:
                        d.value -= 1
        else:
            for j in range(s.table):
                bake(j)
                if j != s.table - 1:
                    d.value -= 1

        if s.chunks == 1:
            blit(0)
            return
        if s.chunks == 2:
            with IfAll(index <= chunk - 1):
                blit(0)
            with Else:
                blit(1)
            return

        if s.lone:
            # The lone chunk's condition is exact, so it needs no gating and
            # runs first, while the payloads are still fully alive.
            with IfAll(index >= (s.chunks - 1) * chunk):
                blit(s.chunks - 1)
            kill(gate_flag(s.pairs - 1))
        for a in range(s.pairs - 1, -1, -1):
            low_chunk = 2 * a
            start = low_chunk * chunk
            with IfAll(index >= start, index <= start + chunk - 1):
                blit(low_chunk)
            with Else:
                blit(low_chunk + 1)
            if a > 0:
                for payload, stash in zip(payloads, stashes, strict=True):
                    payload.value = stash
                kill(gate_flag(a - 1))


def _slow_write_costs(n: int, width: int) -> tuple[int, int]:
    best: tuple[int, int] = (n, n * width)
    for hoist in (False, True):
        max_cs = (25 if hoist else 23) // width
        for cs in range(1, min(max_cs, n - 1) + 1):
            chunks = math.ceil(n / cs)
            conditionals = 2 * chunks - 1 + cs
            bookkeeping = 0 if hoist else 2
            expressions = (
                (3 if hoist else 0)
                + (chunks - 1) * (cs * width + bookkeeping)
                + cs * width
                + (0 if hoist else 1)
                + cs * width
                + n * width
            )
            if (conditionals, expressions) < best:
                best = (conditionals, expressions)
    return best


def _fast_write_plan(
    *,
    items: Sequence[Sequence[Editable]],
    n: int,
    width: int,
) -> tuple[list[ColumnInfo], int] | None:
    if not all(
        isinstance(slot, Stat) and slot.internal_type is InternalType.LONG
        for item in items
        for slot in item
    ):
        return None
    pattern = _detect_pattern(items)
    if pattern is None:
        return None
    # The fast path keys its one-hot lookups on composed names in the `hw`
    # namespace (and stage slots in `sw`/`tmp` ones). Items living in those
    # namespaces would collide with the machinery, so they take the cascade.
    if any(
        prefix.startswith(('hw', 'sw', 'tmp'))
        for _cls, prefix, _suffix, _coeff, _offset in pattern
    ):
        return None

    best: tuple[tuple[int, int], int] | None = None
    for chunk in range(1, _BE_LIMIT // width + 1):
        cost = _fast_write_costs(n, width, chunk)
        if best is None or cost < best[0]:
            best = (cost, chunk)
    if best is None:
        return None
    cost, chunk = best
    if cost >= _slow_write_costs(n, width):
        return None
    if _in_nested_container() and (cost[0] > 0 or cost[1] > _BE_LIMIT):
        # Inside a conditional there is no room to grow: another conditional
        # cannot be nested, and neither can the Random that would otherwise buy
        # room. Defer to the cascade so the caller gets its clear "cannot nest"
        # error rather than a limit failure from deep inside the fixer.
        return None
    return pattern, chunk


def cheap_read(
    *,
    items: Sequence[MaybeSequence[Checkable | HousingType]],
    index: Editable,
    output: MaybeSequence[Editable],
) -> None:
    items = [into_sequence(item) for item in items]
    output = into_sequence(output)

    if len(items) == 0:
        raise ValueError('Cannot read from an empty list')
    width = assert_same_widths((*items, output))
    if width > 12:
        raise ValueError(f'Tuple width {width} exceeds the supported maximum of 12')

    pattern = _detect_pattern(items)
    if pattern is not None:
        _emit_fast_read(pattern=pattern, index=index, output=output)
        return

    is_start = True

    while len(items) > 4:
        part_size = min(24 // width, (len(items) + 1) // 2)
        new_items: list[tuple[Editable, ...]] = [
            make_temps(i, items[0]) for i in range(part_size)
        ]

        chunk_starts = list(range(part_size, len(items), part_size))
        for idx, chunk_start in enumerate(chunk_starts):
            chunk_end = min(chunk_start + part_size, len(items))
            with IfAll(index >= chunk_start, index < chunk_end):
                index.value -= chunk_start
                for i, j in enumerate(range(chunk_start, chunk_end)):
                    assign(new_items[i], items[j])
            if is_start and idx == 0:
                with Else:
                    for i in range(part_size):
                        assign(new_items[i], items[i])

        is_start = False
        items = new_items

    if len(items) == 1:
        assign(output, items[0])
    elif len(items) == 2:
        with IfAll(index == 0):
            assign(output, items[0])
        with Else:
            assign(output, items[1])
    elif len(items) == 3:
        with IfAll(index < 2):
            assign(output, items[1])
        with Else:
            assign(output, items[2])
        with IfAll(index == 0):
            assign(output, items[0])
    else:  # len(items) == 4
        temp_stat = make_temps(0, items[0])
        with IfAll(index < 2):
            assign(temp_stat, items[0])
            assign(output, items[1])
        with Else:
            assign(temp_stat, items[2])
            assign(output, items[3])
        with IfAny(index == 0, index == 2):
            assign(output, temp_stat)


def cheap_write(
    *,
    items: Sequence[MaybeSequence[Editable]],
    index: Editable,
    input: MaybeSequence[Checkable | HousingType],
) -> None:
    items = [into_sequence(item) for item in items]
    input = into_sequence(input)

    if len(items) == 0:
        raise ValueError('Cannot write to an empty list')
    width = assert_same_widths((*items, input))
    if width > 12:
        raise ValueError(f'Tuple width {width} exceeds the supported maximum of 12')

    n = len(items)

    if n == 1:
        assign(items[0], input)
        return

    fast = _fast_write_plan(items=items, n=n, width=width)
    if fast is not None:
        pattern, chunk = fast
        _emit_fast_write(
            pattern=pattern,
            items=items,
            index=index,
            input=input,
            chunk=chunk,
        )
        return

    best_ce = n
    best_be = 0
    best_cs = 0
    best_hoist = False
    for hoist in (False, True):
        max_cs = (25 if hoist else 23) // width
        be = 2 if hoist else 0
        for cs in range(1, min(max_cs, n - 1) + 1):
            ce = 2 * math.ceil(n / cs) - 1 + cs
            if (ce, be) < (best_ce, best_be):
                best_ce, best_be, best_cs, best_hoist = ce, be, cs, hoist

    if best_cs == 0:
        for i, item in enumerate(items):
            with IfAll(index == i):
                assign(item, input)
        return

    chunk_size = best_cs
    hoist = best_hoist
    temp_stats: list[tuple[Editable, ...]] = [
        make_temps(j, items[0]) for j in range(chunk_size)
    ]
    chunk_idx_stat = PlayerStat(f'tmp{chunk_size * width}').as_long()

    if hoist:
        chunk_idx_stat.value = index // chunk_size
        index.value -= chunk_idx_stat * chunk_size

    chunk_starts = list(range(0, n, chunk_size))
    for chunk_idx, chunk_start in enumerate(chunk_starts[1:], start=1):
        chunk_end = min(chunk_start + chunk_size, n)
        if hoist:
            with IfAll(chunk_idx_stat == chunk_idx):
                for j, item in enumerate(items[chunk_start:chunk_end]):
                    assign(temp_stats[j], item)
        else:
            with IfAll(index >= chunk_start, index < chunk_end):
                for j, item in enumerate(items[chunk_start:chunk_end]):
                    assign(temp_stats[j], item)
                index.value -= chunk_start
                chunk_idx_stat.value = chunk_idx
        if chunk_idx == 1:
            with Else:
                for j, item in enumerate(items[:chunk_size]):
                    assign(temp_stats[j], item)
                if not hoist:
                    chunk_idx_stat.value = 0

    for j in range(chunk_size):
        with IfAll(index == j):
            assign(temp_stats[j], input)

    for chunk_idx, chunk_start in enumerate(chunk_starts):
        chunk_end = min(chunk_start + chunk_size, n)
        with IfAll(chunk_idx_stat == chunk_idx):
            for j, item in enumerate(items[chunk_start:chunk_end]):
                assign(item, temp_stats[j])
