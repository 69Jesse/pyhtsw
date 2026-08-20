import math
import random

from helpers import expect_exception
from pyhtsw.actions.conditional.statements import IfAll
from pyhtsw.actions.random import RandomExpression
from pyhtsw.ext.cheap_read_write import cheap_read, cheap_write

from pyhtsw import Container, ExecutionContext, GlobalStat, PlayerStat
from pyhtsw.expression.binary_expression import BinaryExpression
from pyhtsw.expression.condition.conditional_expression import ConditionalExpression


def letter_name(i: int) -> str:
    """0 -> 'a', 1 -> 'b', ..., 25 -> 'z', 26 -> 'aa', 27 -> 'ab', ..., 51 -> 'az', 52 -> 'ba'.

    Spreadsheet-column-style encoding. Used to defeat cheap_read's fast path,
    which only triggers when names form `prefix + format(start + i, ',') + suffix`.
    """
    parts = []
    n = i
    while True:
        parts.append(chr(ord('a') + n % 26))
        n = n // 26 - 1
        if n < 0:
            break
    return ''.join(reversed(parts))


def sample_targets(length: int) -> list[int]:
    return random.sample(range(length), min(20, length))


def value_at(i: int, k: int) -> int:
    return i * 1000 + k + 1  # nonzero so a read into a default-0 stat is detectable


for length in (1, 10, 100):
    for width in (1, 3):
        with ExecutionContext(ignore_action_limits=True) as ctx:
            sources = [
                tuple(
                    PlayerStat(letter_name(i * width + k)).as_long()
                    for k in range(width)
                )
                for i in range(length)
            ]
            for i in range(length):
                for k in range(width):
                    ctx.put(sources[i][k], value_at(i, k))

            items_arg = [s[0] for s in sources] if width == 1 else list(sources)

            index = PlayerStat('idx').as_long()
            outputs = tuple(PlayerStat(f'o{k}').as_long() for k in range(width))
            output_arg = outputs[0] if width == 1 else outputs

            for target in sample_targets(length):
                index.value = target
                cheap_read(items=items_arg, index=index, output=output_arg)

                def check_read(
                    _w: int = width,
                    _len: int = length,
                    _t: int = target,
                    _outs: tuple[PlayerStat, ...] = outputs,
                ) -> None:
                    for k in range(_w):
                        got = int(ctx.get(_outs[k]))
                        want = value_at(_t, k)
                        assert got == want, (
                            f'read width={_w} length={_len} target={_t}: '
                            f'output[{k}]={got}, want {want}'
                        )

                ctx.assert_all(check_read)


NEW_OFFSET = 1_000_000  # added to value_at to make the post-write value distinct


for length in (1, 10, 100):
    for width in (1, 3):
        with ExecutionContext(ignore_action_limits=True) as ctx:
            slots = [
                tuple(
                    PlayerStat(letter_name(i * width + k)).as_long()
                    for k in range(width)
                )
                for i in range(length)
            ]
            for i in range(length):
                for k in range(width):
                    ctx.put(slots[i][k], value_at(i, k))

            index = PlayerStat('idx').as_long()
            items_arg = [s[0] for s in slots] if width == 1 else list(slots)
            promoted: set[int] = set()

            for target in sample_targets(length):
                promoted.add(target)
                index.value = target
                new_inputs = tuple(
                    value_at(target, k) + NEW_OFFSET for k in range(width)
                )
                input_arg = new_inputs[0] if width == 1 else new_inputs

                cheap_write(items=items_arg, index=index, input=input_arg)

                def check_write(
                    _w: int = width,
                    _len: int = length,
                    _t: int = target,
                    _slots: list[tuple[PlayerStat, ...]] = slots,
                    _promoted: frozenset[int] = frozenset(promoted),
                ) -> None:
                    for i in range(_len):
                        for k in range(_w):
                            got = int(ctx.get(_slots[i][k]))
                            want = value_at(i, k) + (
                                NEW_OFFSET if i in _promoted else 0
                            )
                            assert got == want, (
                                f'write width={_w} length={_len} target={_t}: '
                                f'item[{i}][{k}]={got}, want {want}'
                            )

                ctx.assert_all(check_write)


# Width=1, non-empty prefix, simple indexing → 4 BinaryExpressions, no conditionals.
with Container() as container:
    sources = [PlayerStat(f'src{i}').as_long() for i in range(10)]
    idx = PlayerStat('idx').as_long()
    out = PlayerStat('out').as_long()
    cheap_read(items=sources, index=idx, output=out)

counts = container.expression_counts(nested=True)
assert len(counts) == 1, counts
assert counts[BinaryExpression] == 4, counts


# Width=1, empty prefix (names are just digits) → still 4 BinaryExpressions:
# the scope head must ride in the prefix variable even with no shared prefix,
# because a literal `%var.player/` next to the counter placeholder is eaten by
# htsw's parseString (its `%` pairs with the counter's opening `%`).
with Container() as container:
    sources = [PlayerStat(f'{i}').as_long() for i in range(10)]
    idx = PlayerStat('idx').as_long()
    out = PlayerStat('out').as_long()
    cheap_read(items=sources, index=idx, output=out)

counts = container.expression_counts(nested=True)
assert len(counts) == 1, counts
assert counts[BinaryExpression] == 4, counts


# Width=3 Mode A (shared prefix, flat numbering) → 10 BinaryExpressions: the
# one shared prefix bake serves all three columns.
with Container() as container:
    items = [
        tuple(PlayerStat(f'a{i * 3 + k}').as_long() for k in range(3))
        for i in range(10)
    ]
    idx = PlayerStat('idx').as_long()
    o = tuple(PlayerStat(f'o{k}').as_long() for k in range(3))
    cheap_read(items=items, index=idx, output=o)

counts = container.expression_counts(nested=True)
assert len(counts) == 1, counts
assert counts[BinaryExpression] == 10, counts


# Width=3 Mode B (per-column independent prefix) → 12 BinaryExpressions.
with Container() as container:
    items = [
        (
            PlayerStat(f'aaa{i}').as_long(),
            PlayerStat(f'bbb{i}').as_long(),
            PlayerStat(f'ccc{i}').as_long(),
        )
        for i in range(10)
    ]
    idx = PlayerStat('idx').as_long()
    o = tuple(PlayerStat(f'o{k}').as_long() for k in range(3))
    cheap_read(items=items, index=idx, output=o)

counts = container.expression_counts(nested=True)
assert len(counts) == 1, counts
assert counts[BinaryExpression] == 12, counts


# GlobalStat fast path → 4 BinaryExpressions (same shape as PlayerStat).
with Container() as container:
    sources = [GlobalStat(f'gsrc{i}').as_long() for i in range(10)]
    idx = PlayerStat('idx').as_long()
    out = PlayerStat('out').as_long()
    cheap_read(items=sources, index=idx, output=out)

counts = container.expression_counts(nested=True)
assert len(counts) == 1, counts
assert counts[BinaryExpression] == 4, counts


# Middle-digit increment (`a101a, a111a, a121a, ...`) → still fast path.
with Container() as container:
    sources = [PlayerStat(f'a1{i}1a').as_long() for i in range(10)]
    idx = PlayerStat('idx').as_long()
    out = PlayerStat('out').as_long()
    cheap_read(items=sources, index=idx, output=out)

counts = container.expression_counts(nested=True)
assert len(counts) == 1, counts
assert counts[BinaryExpression] == 4, counts


# Comma boundary: names cross 999 -> 1,000 with comma formatting -> fast path.
with Container() as container:
    sources = [PlayerStat(f'a{i:,}').as_long() for i in range(999, 1010)]
    idx = PlayerStat('idx').as_long()
    out = PlayerStat('out').as_long()
    cheap_read(items=sources, index=idx, output=out)

counts = container.expression_counts(nested=True)
assert len(counts) == 1, counts
assert counts[BinaryExpression] == 4, counts


# Comma boundary correctness: substitution applies comma formatting (mirrors
# HTSL behavior), so reading items[i] for i straddling the 999/1,000 boundary
# resolves to the correct stat.
for _target in (0, 1, 4, 10):  # 0 -> a999, 1 -> a1,000, 10 -> a1,009
    with ExecutionContext(ignore_action_limits=True) as ctx:
        _sources = [PlayerStat(f'a{i:,}').as_long() for i in range(999, 1010)]
        for _i, _s in enumerate(_sources):
            ctx.put(_s, 1_000_000 + _i)
        _idx = PlayerStat('idx').as_long()
        _out = PlayerStat('out').as_long()
        _idx.value = _target
        cheap_read(items=_sources, index=_idx, output=_out)

        def check_comma(
            _t: int = _target,
            _o: PlayerStat = _out,
        ) -> None:
            got = int(ctx.get(_o))
            assert got == 1_000_000 + _t, (got, _t)

        ctx.assert_all(check_comma)


# No-comma names crossing 1000 boundary: pattern detection bails (since
# format(1000, ',') == '1,000' != '1000') -> falls back to slow path.
with Container() as container:
    sources = [PlayerStat(f'a{i}').as_long() for i in range(999, 1010)]
    idx = PlayerStat('idx').as_long()
    out = PlayerStat('out').as_long()
    cheap_read(items=sources, index=idx, output=out)

counts = container.expression_counts(nested=True)
assert len(counts) == 2, counts
assert counts[BinaryExpression] > 5, counts
assert counts[ConditionalExpression] > 1, counts


# Mixing PlayerStat and GlobalStat in the same items -> fast-path bails.
with Container() as container:
    sources = [
        PlayerStat('mix0').as_long(),
        GlobalStat('mix1').as_long(),
        PlayerStat('mix2').as_long(),
    ]
    idx = PlayerStat('idx').as_long()
    out = PlayerStat('out').as_long()
    cheap_read(items=sources, index=idx, output=out)

counts = container.expression_counts(nested=True)
assert len(counts) == 2, counts
assert ConditionalExpression in counts, counts


# Plain integer literals as items -> not stats at all -> slow path.
with Container() as container:
    idx = PlayerStat('idx').as_long()
    out = PlayerStat('out').as_long()
    cheap_read(items=[10, 20, 30, 40, 50], index=idx, output=out)

counts = container.expression_counts(nested=True)
assert len(counts) == 2, counts
assert ConditionalExpression in counts, counts


# Width=1, PlayerStat, prefix='src', start=0
for _target in (0, 3, 7, 9):
    with ExecutionContext(ignore_action_limits=True) as ctx:
        _sources = [PlayerStat(f'src{i}').as_long() for i in range(10)]
        for _i, _s in enumerate(_sources):
            ctx.put(_s, 100 + _i)
        _idx = PlayerStat('idx').as_long()
        _out = PlayerStat('out').as_long()
        _idx.value = _target
        cheap_read(items=_sources, index=_idx, output=_out)

        def check_w1_player(
            _t: int = _target,
            _o: PlayerStat = _out,
        ) -> None:
            got = int(ctx.get(_o))
            assert got == 100 + _t, (got, _t)

        ctx.assert_all(check_w1_player)


# Width=1, GlobalStat
for _target in (0, 4, 9):
    with ExecutionContext(ignore_action_limits=True) as ctx:
        _sources = [GlobalStat(f'gsrc{i}').as_long() for i in range(10)]
        for _i, _s in enumerate(_sources):
            ctx.put(_s, 200 + _i)
        _idx = PlayerStat('idx').as_long()
        _out = PlayerStat('out').as_long()
        _idx.value = _target
        cheap_read(items=_sources, index=_idx, output=_out)

        def check_w1_global(
            _t: int = _target,
            _o: PlayerStat = _out,
        ) -> None:
            got = int(ctx.get(_o))
            assert got == 200 + _t, (got, _t)

        ctx.assert_all(check_w1_global)


# Width=3, Mode B (per-column prefixes)
for _target in (0, 2, 5, 7):
    with ExecutionContext(ignore_action_limits=True) as ctx:
        _items = [
            (
                PlayerStat(f'aaa{i}').as_long(),
                PlayerStat(f'bbb{i}').as_long(),
                PlayerStat(f'ccc{i}').as_long(),
            )
            for i in range(8)
        ]
        for _i, _row in enumerate(_items):
            for _k, _s in enumerate(_row):
                ctx.put(_s, _i * 10 + _k)
        _idx = PlayerStat('idx').as_long()
        _outputs = tuple(PlayerStat(f'o{k}').as_long() for k in range(3))
        _idx.value = _target
        cheap_read(items=_items, index=_idx, output=_outputs)

        def check_w3_modeB(
            _t: int = _target,
            _outs: tuple[PlayerStat, ...] = _outputs,
        ) -> None:
            for k in range(3):
                got = int(ctx.get(_outs[k]))
                assert got == _t * 10 + k, (got, _t, k)

        ctx.assert_all(check_w3_modeB)


# Width=3, Mode A (shared prefix, flat numbering)
for _target in (0, 3, 7):
    with ExecutionContext(ignore_action_limits=True) as ctx:
        _items = [
            tuple(PlayerStat(f'm{i * 3 + k}').as_long() for k in range(3))
            for i in range(8)
        ]
        for _i, _row in enumerate(_items):
            for _k, _s in enumerate(_row):
                ctx.put(_s, _i * 100 + _k)
        _idx = PlayerStat('idx').as_long()
        _outputs = tuple(PlayerStat(f'o{k}').as_long() for k in range(3))
        _idx.value = _target
        cheap_read(items=_items, index=_idx, output=_outputs)

        def check_w3_modeA(
            _t: int = _target,
            _outs: tuple[PlayerStat, ...] = _outputs,
        ) -> None:
            for k in range(3):
                got = int(ctx.get(_outs[k]))
                assert got == _t * 100 + k, (got, _t, k)

        ctx.assert_all(check_w3_modeA)


# Middle-digit pattern correctness ('a1<n>1a')
for _target in (0, 3, 6, 9):
    with ExecutionContext(ignore_action_limits=True) as ctx:
        _sources = [PlayerStat(f'a1{i}1a').as_long() for i in range(10)]
        for _i, _s in enumerate(_sources):
            ctx.put(_s, 7000 + _i)
        _idx = PlayerStat('idx').as_long()
        _out = PlayerStat('out').as_long()
        _idx.value = _target
        cheap_read(items=_sources, index=_idx, output=_out)

        def check_middle(
            _t: int = _target,
            _o: PlayerStat = _out,
        ) -> None:
            got = int(ctx.get(_o))
            assert got == 7000 + _t, (got, _t)

        ctx.assert_all(check_middle)


# Non-zero start (offset != 0): items 'p5'..'p14', logical index 0..9
for _target in (0, 3, 9):
    with ExecutionContext(ignore_action_limits=True) as ctx:
        _sources = [PlayerStat(f'p{i}').as_long() for i in range(5, 15)]
        for _i, _s in enumerate(_sources):
            ctx.put(_s, 500 + _i)
        _idx = PlayerStat('idx').as_long()
        _out = PlayerStat('out').as_long()
        _idx.value = _target
        cheap_read(items=_sources, index=_idx, output=_out)

        def check_offset(
            _t: int = _target,
            _o: PlayerStat = _out,
        ) -> None:
            got = int(ctx.get(_o))
            assert got == 500 + _t, (got, _t)

        ctx.assert_all(check_offset)


# Empty items list
with expect_exception(ValueError):
    cheap_read(
        items=[],
        index=PlayerStat('idx').as_long(),
        output=PlayerStat('out').as_long(),
    )

# Mismatched widths within items
with expect_exception(ValueError):
    cheap_read(
        items=[(1, 2), (3, 4, 5)],
        index=PlayerStat('idx').as_long(),
        output=(PlayerStat('a').as_long(), PlayerStat('b').as_long()),
    )

# Output width doesn't match items width
with expect_exception(ValueError):
    cheap_read(
        items=[(1, 2), (3, 4)],
        index=PlayerStat('idx').as_long(),
        output=PlayerStat('a').as_long(),
    )

# Width exceeds the supported maximum (12)
big = tuple(range(13))
with expect_exception(ValueError):
    cheap_read(
        items=[big, big],
        index=PlayerStat('idx').as_long(),
        output=tuple(PlayerStat(f'o{k}').as_long() for k in range(13)),
    )


for _width in (1, 2, 3):
    with ExecutionContext(ignore_action_limits=True) as ctx:
        _items = [
            tuple(PlayerStat(f'z{i * _width + k}').as_long() for k in range(_width))
            for i in range(4)
        ]
        for _i, _row in enumerate(_items):
            for _k, _s in enumerate(_row):
                ctx.put(_s, _i * 100 + _k + 1)
        _idx = PlayerStat('idx').as_long()
        _idx.value = 0
        _outputs = tuple(PlayerStat(f'o{k}').as_long() for k in range(_width))
        cheap_read(
            items=_items if _width > 1 else [row[0] for row in _items],
            index=_idx,
            output=_outputs if _width > 1 else _outputs[0],
        )

        def check_zero_index(
            _w: int = _width,
            _outs: tuple[PlayerStat, ...] = _outputs,
        ) -> None:
            for k in range(_w):
                got = int(ctx.get(_outs[k]))
                assert got == k + 1, (
                    f'width={_w} index=0: output[{k}]={got}, want {k + 1}'
                )

        ctx.assert_all(check_zero_index)


for _length, _width in ((2, 1), (5, 1), (13, 1), (30, 1), (60, 1), (6, 2), (10, 3)):
    for _target in sample_targets(_length):
        with ExecutionContext(ignore_action_limits=True) as ctx:
            _slots = [
                tuple(
                    PlayerStat(f'fw{i * _width + k}').as_long() for k in range(_width)
                )
                for i in range(_length)
            ]
            for _i in range(_length):
                for _k in range(_width):
                    ctx.put(_slots[_i][_k], value_at(_i, _k))
            _idx = PlayerStat('idx').as_long()
            _idx.value = _target
            _new = tuple(-7_000_000 - k for k in range(_width))

            cheap_write(
                items=[s[0] for s in _slots] if _width == 1 else list(_slots),
                index=_idx,
                input=_new[0] if _width == 1 else _new,
            )

            def check_fast_write(
                _len: int = _length,
                _w: int = _width,
                _t: int = _target,
                _s: list[tuple[PlayerStat, ...]] = _slots,
                _n: tuple[int, ...] = _new,
            ) -> None:
                for i in range(_len):
                    for k in range(_w):
                        got = int(ctx.get(_s[i][k]))
                        want = _n[k] if i == _t else value_at(i, k)
                        assert got == want, (
                            f'fast write length={_len} width={_w} target={_t}: '
                            f'slot[{i}][{k}]={got}, want {want}'
                        )

            ctx.assert_all(check_fast_write)


# Writing the value a slot already holds is a no-op: the diff is 0, which
# auto-unsets the one-hot so every lookup falls back to 0.
for _target in (0, 3, 7):
    with ExecutionContext(ignore_action_limits=True) as ctx:
        _slots = [PlayerStat(f'fz{i}').as_long() for i in range(8)]
        for _s in _slots:
            ctx.put(_s, 42)
        _idx = PlayerStat('idx').as_long()
        _idx.value = _target
        cheap_write(items=_slots, index=_idx, input=42)

        def check_no_op(_s: list[PlayerStat] = _slots, _t: int = _target) -> None:
            for i, stat in enumerate(_s):
                got = int(ctx.get(stat))
                assert got == 42, f'no-op target={_t}: slot[{i}]={got}, want 42'

        ctx.assert_all(check_no_op)


# Successive writes in one block: each one must see the array the previous one
# left behind. The one-hot is only ever read through a name assembled at
# runtime, so nothing in the emitted expressions mentions it -- without a
# keep-alive reference the dead-store pass drops every write but the last.
with ExecutionContext(ignore_action_limits=True) as ctx:
    _slots = [PlayerStat(f'fs{i}').as_long() for i in range(13)]
    for _i, _s in enumerate(_slots):
        ctx.put(_s, value_at(_i, 0))
    _idx = PlayerStat('idx').as_long()
    _written: dict[int, int] = {}
    for _step, _target in enumerate((1, 5, 12, 0)):
        _written[_target] = -5_000 - _step
        _idx.value = _target
        cheap_write(items=_slots, index=_idx, input=_written[_target])

        def check_successive(
            _s: list[PlayerStat] = _slots,
            _w: tuple[tuple[int, int], ...] = tuple(_written.items()),
            _t: int = _target,
        ) -> None:
            _w = dict(_w)  # type: ignore[assignment]
            for i, stat in enumerate(_s):
                got = int(ctx.get(stat))
                want = _w.get(i, value_at(i, 0))
                assert got == want, (
                    f'successive write (after target={_t}): '
                    f'slot[{i}]={got}, want {want}'
                )

        ctx.assert_all(check_successive)


# The fast path costs far fewer conditionals than the chunked cascade, and for
# arrays of any real size fewer expressions too. One conditional per chunk of
# blits is irreducible: a branch holds 25 actions, and Housing forbids nesting a
# conditional inside a conditional, so there is no cheaper way to pick a chunk.
_FAST_WRITE_COUNTS = {
    # length: (conditionals, var changes)
    10: (1, 31),  # small table, full rebake, one wrapped blit chunk
    # Larger arrays split-scatter: half the baked table is rebaked per call
    # inside one if/else, then one exact-range conditional per gather chunk.
    # The overhead is a constant ~67 actions - packing chunks into else arms
    # was abandoned because every extra else needs a payload liveness
    # transition (a wrapper conditional plus gate arithmetic) and executes a
    # spurious blit list per call, buying back only ~1 conditional each.
    100: (5, 166),
    1000: (41, 1066),
}
for _length, (_want_cond, _want_be) in _FAST_WRITE_COUNTS.items():
    with Container() as container:
        cheap_write(
            items=[PlayerStat(f'w{i:,}').as_long() for i in range(_length)],
            index=PlayerStat('idx').as_long(),
            input=PlayerStat('inp').as_long(),
        )
    counts = container.expression_counts(nested=True)
    assert counts.get(ConditionalExpression, 0) == _want_cond, (_length, counts)
    assert counts.get(BinaryExpression, 0) == _want_be, (_length, counts)
    assert counts.get(RandomExpression, 0) == 0, (_length, counts)

# Four of the 100-slot conditionals are the exact-range gather chunks; the
# scatter if/else accounts for the fifth.
assert _FAST_WRITE_COUNTS[100][0] >= math.ceil(100 / 25)

# With the enclosing action list already full, the ~18-action setup costs one
# wrapper conditional on top: wrapped setup, the scatter if/else, and one
# exact-range conditional per chunk. (A 5-conditional shape exists - pair the
# chunks into two if/elses with a gated midway - but it trades ~18 emitted
# and ~65 *executed* actions for that one conditional, so it was dropped.)
with Container() as container:
    for _ in range(25):
        PlayerStat('ignoreme1').value += PlayerStat('ignoreme2')
    cheap_write(
        items=[PlayerStat(f'item{i}').as_long() for i in range(100)],
        index=PlayerStat('index').as_long(),
        input=PlayerStat('input').as_long(),
    )
counts = container.expression_counts()
assert counts.get(ConditionalExpression, 0) == 6, counts
counts = container.expression_counts(nested=True)
assert counts.get(RandomExpression, 0) == 0, counts


# Neither a conditional nor a Random can be nested inside a conditional, so a
# cheap_write that needs either cannot be emitted from inside one. That has
# always been true of the cascade; the fast path defers to it rather than
# failing later inside the limit fixer.
with expect_exception(SyntaxError):
    with Container():
        with IfAll(PlayerStat('gate').as_long() == 1):
            cheap_write(
                items=[PlayerStat(f'q{i}').as_long() for i in range(100)],
                index=PlayerStat('idx').as_long(),
                input=PlayerStat('inp').as_long(),
            )

# A write small enough to fit one action list needs neither, so it still works.
with Container() as container:
    with IfAll(PlayerStat('gate').as_long() == 1):
        cheap_write(
            items=[PlayerStat(f'r{i}').as_long() for i in range(3)],
            index=PlayerStat('idx').as_long(),
            input=PlayerStat('inp').as_long(),
        )
counts = container.expression_counts(nested=True)
assert counts.get(RandomExpression, 0) == 0, counts


# The one-hot patch is arithmetic, so non-LONG slots take the staged write:
# a conditional-free composed load of the target chunk, sqrt(n)-ish select
# conditionals, and one exact-range store conditional per chunk.
for _stats in (
    [PlayerStat(f'd{i}').as_double() for i in range(30)],
    [PlayerStat(f's{i}').as_string() for i in range(30)],
):
    with Container() as container:
        cheap_write(
            items=_stats,
            index=PlayerStat('idx').as_long(),
            input=_stats[0],
        )
    counts = container.expression_counts(nested=True)
    assert counts.get(ConditionalExpression, 0) == 11, counts


# Names that don't form an arithmetic run have no dynamic read, so likewise.
with Container() as container:
    cheap_write(
        items=[PlayerStat(letter_name(i)).as_long() for i in range(30)],
        index=PlayerStat('idx').as_long(),
        input=PlayerStat('inp').as_long(),
    )
counts = container.expression_counts(nested=True)
assert counts.get(ConditionalExpression, 0) > 10, counts


# Exhaustive index sweep at the headline size.
with ExecutionContext(ignore_action_limits=True) as ctx:
    _slots = [PlayerStat(f'fx{i}').as_long() for i in range(100)]
    for _i, _s in enumerate(_slots):
        ctx.put(_s, value_at(_i, 0))
    _idx = PlayerStat('idx').as_long()
    _expected = [value_at(_i, 0) for _i in range(100)]
    for _target in range(100):
        _idx.value = _target
        _new = -3_000_000 - _target
        _expected[_target] = _new
        cheap_write(items=_slots, index=_idx, input=_new)

    def check_fw_exhaustive(
        _s: list[PlayerStat] = _slots,
        _want: list[int] = _expected,
    ) -> None:
        for i, stat in enumerate(_s):
            got = int(ctx.get(stat))
            assert got == _want[i], (
                f'fast-write sweep: slot[{i}]={got}, want {_want[i]}'
            )

    ctx.assert_all(check_fw_exhaustive)


# Extreme magnitudes: the diff wraps modulo 2**64, and the wrap cancels so the
# slot still lands exactly on the input.
for _old, _new in (
    (2**63 - 1, -(2**63)),
    (-(2**63), 2**63 - 1),
    (2**63 - 1, 2**63 - 1),
    (-1, 1),
    (0, 2**63 - 1),
    (2**63 - 1, 0),
):
    for _target in (0, 13, 24, 25, 99):
        with ExecutionContext(ignore_action_limits=True) as ctx:
            _slots = [PlayerStat(f'fy{i}').as_long() for i in range(100)]
            for _i, _s in enumerate(_slots):
                ctx.put(_s, _old)
            _idx = PlayerStat('idx').as_long()
            _idx.value = _target
            cheap_write(items=_slots, index=_idx, input=_new)

            def check_fw_extreme(
                _s: list[PlayerStat] = _slots,
                _t: int = _target,
                _o: int = _old,
                _n: int = _new,
            ) -> None:
                for i, stat in enumerate(_s):
                    got = int(ctx.get(stat))
                    want = _n if i == _t else _o
                    assert got == want, (
                        f'fast-write extremes old={_o} new={_n} target={_t}: '
                        f'slot[{i}]={got}, want {want}'
                    )

            ctx.assert_all(check_fw_extreme)


# Non-zero start and a comma boundary in the composed names.
for _start, _len in ((100, 30), (990, 20)):
    for _target in (0, 7, 8, 15, 16, _len - 1):
        with ExecutionContext(ignore_action_limits=True) as ctx:
            _slots = [PlayerStat(f'n{_start + i:,}').as_long() for i in range(_len)]
            for _i, _s in enumerate(_slots):
                ctx.put(_s, value_at(_i, 0))
            _idx = PlayerStat('idx').as_long()
            _idx.value = _target
            cheap_write(items=_slots, index=_idx, input=-42_424)

            def check_fw_start(
                _s: list[PlayerStat] = _slots,
                _t: int = _target,
                _st: int = _start,
            ) -> None:
                for i, stat in enumerate(_s):
                    got = int(ctx.get(stat))
                    want = -42_424 if i == _t else value_at(i, 0)
                    assert got == want, (
                        f'fast-write start={_st}: slot[{i}]={got}, want {want}'
                    )

            ctx.assert_all(check_fw_start)


# GlobalStat arrays route the composed read through var.global while the
# helper's own bookkeeping stays player-side.
with ExecutionContext(ignore_action_limits=True) as ctx:
    _gslots = [GlobalStat(f'g{i}').as_long() for i in range(40)]
    for _i, _s in enumerate(_gslots):
        ctx.put(_s, value_at(_i, 0))
    _idx = PlayerStat('idx').as_long()
    for _target in (0, 24, 25, 39):
        _idx.value = _target
        cheap_write(items=_gslots, index=_idx, input=7_777_000 + _target)

    def check_fw_global(_s: list[GlobalStat] = _gslots) -> None:
        for i, stat in enumerate(_s):
            got = int(ctx.get(stat))
            want = 7_777_000 + i if i in (0, 24, 25, 39) else value_at(i, 0)
            assert got == want, f'fast-write global: slot[{i}]={got}, want {want}'

    ctx.assert_all(check_fw_global)


# Items whose shared prefix is a single letter would collide with a temp of
# the same name: htsw's parseString replaces each placeholder at its FIRST
# occurrence, so a counter named like the prefix would match inside the
# freshly inserted prefix text and mangle the composed name. The name pool
# skips such letters; this pins the guard for both the read and the write.
with ExecutionContext(ignore_action_limits=True) as ctx:
    _aslots = [PlayerStat(f'a{i}').as_long() for i in range(60)]
    for _i, _s in enumerate(_aslots):
        ctx.put(_s, 3_000 + _i)
    _idx = PlayerStat('idx').as_long()
    _idx.value = 42
    cheap_write(items=_aslots, index=_idx, input=424_242)

    def check_fw_prefix_collision(_s: list[PlayerStat] = _aslots) -> None:
        for i, stat in enumerate(_s):
            got = int(ctx.get(stat))
            want = 424_242 if i == 42 else 3_000 + i
            assert got == want, f'prefix-collision write: slot[{i}]={got}, want {want}'

    ctx.assert_all(check_fw_prefix_collision)


# Items living inside the helper's own one-hot namespaces cannot use the fast
# paths at all — the composed keys would read the items themselves.
with Container() as container:
    cheap_write(
        items=[PlayerStat(f'hw{i}').as_long() for i in range(30)],
        index=PlayerStat('idx').as_long(),
        input=PlayerStat('inp').as_long(),
    )
counts = container.expression_counts(nested=True)
assert counts.get(ConditionalExpression, 0) > 10, counts


with ExecutionContext(ignore_action_limits=True) as ctx:
    _slots = [PlayerStat(f'vf{i}').as_long() for i in range(100)]
    for _i, _s in enumerate(_slots):
        ctx.put(_s, value_at(_i, 0))
    _idx = PlayerStat('idx').as_long()
    _written = {}
    for _step, _target in enumerate(
        (20, 3, 70, 12, 13, 99, 0, 50, 74, 75, 25, 24, 49, 62, 62),
    ):
        _written[_target] = -9_000 - _step
        _idx.value = _target
        cheap_write(items=_slots, index=_idx, input=_written[_target])

        def check_v5_successive(
            _s: list[PlayerStat] = _slots,
            _w: tuple[tuple[int, int], ...] = tuple(_written.items()),
            _t: int = _target,
        ) -> None:
            _w = dict(_w)  # type: ignore[assignment]
            for i, stat in enumerate(_s):
                got = int(ctx.get(stat))
                want = _w.get(i, value_at(i, 0))
                assert got == want, (
                    f'v5 successive (after target={_t}): slot[{i}]={got}, want {want}'
                )

        ctx.assert_all(check_v5_successive)


# v5 exhaustive index sweep at the smallest two-chunk size: every target of a
# 26-slot array in one block, so each call also sees every staleness pattern
# the previous ones left behind.
with ExecutionContext(ignore_action_limits=True) as ctx:
    _slots = [PlayerStat(f'vg{i}').as_long() for i in range(26)]
    for _i, _s in enumerate(_slots):
        ctx.put(_s, value_at(_i, 0))
    _idx = PlayerStat('idx').as_long()
    _final = {}
    for _target in range(26):
        _final[_target] = 70_000 + _target
        _idx.value = _target
        cheap_write(items=_slots, index=_idx, input=_final[_target])

    def check_v5_exhaustive(_s: list[PlayerStat] = _slots) -> None:
        for i, stat in enumerate(_s):
            got = int(ctx.get(stat))
            assert got == 70_000 + i, f'v5 exhaustive: slot[{i}]={got}'

    ctx.assert_all(check_v5_exhaustive)


# v5 with a lone chunk (n=75 -> three chunks: one exact-condition lone plus an
# if/else pair) and with a non-zero name offset (names start at 'vh5').
for _n, _first, _targets in ((75, 0, (60, 10, 74, 40)), (30, 5, (0, 29, 13, 12))):
    with ExecutionContext(ignore_action_limits=True) as ctx:
        _slots = [PlayerStat(f'vh{_first + i}').as_long() for i in range(_n)]
        for _i, _s in enumerate(_slots):
            ctx.put(_s, value_at(_i, 0))
        _idx = PlayerStat('idx').as_long()
        _written = {}
        for _step, _target in enumerate(_targets):
            _written[_target] = -3_500 - _step
            _idx.value = _target
            cheap_write(items=_slots, index=_idx, input=_written[_target])

        def check_v5_shapes(
            _s: list[PlayerStat] = _slots,
            _w: tuple[tuple[int, int], ...] = tuple(_written.items()),
            _n_: int = _n,
        ) -> None:
            _w = dict(_w)  # type: ignore[assignment]
            for i, stat in enumerate(_s):
                got = int(ctx.get(stat))
                want = _w.get(i, value_at(i, 0))
                assert got == want, f'v5 n={_n_}: slot[{i}]={got}, want {want}'

        ctx.assert_all(check_v5_shapes)


# v5 GlobalStat array: the machinery stays player-side, only the item scope
# head changes.
with ExecutionContext(ignore_action_limits=True) as ctx:
    _gslots = [GlobalStat(f'vk{i}').as_long() for i in range(40)]
    for _i, _s in enumerate(_gslots):
        ctx.put(_s, value_at(_i, 0))
    _idx = PlayerStat('idx').as_long()
    _idx.value = 33
    cheap_write(items=_gslots, index=_idx, input=-123_456)

    def check_v5_global(_s: list[GlobalStat] = _gslots) -> None:
        for i, stat in enumerate(_s):
            got = int(ctx.get(stat))
            want = -123_456 if i == 33 else value_at(i, 0)
            assert got == want, f'v5 global: slot[{i}]={got}, want {want}'

    ctx.assert_all(check_v5_global)


with ExecutionContext(ignore_action_limits=True) as ctx:
    _sitems = [PlayerStat(f'sv{i}').as_string() for i in range(30)]
    for _i, _s in enumerate(_sitems):
        ctx.put(_s, f'word{_i}', ignore_warning=True)
    ctx.put(_sitems[7], '%var.player/sv3%', ignore_warning=True)
    _idx = PlayerStat('idx').as_long()
    _swritten: dict[int, str] = {}
    for _step, _t in enumerate((0, 12, 25, 29, 7, 12)):
        _swritten[_t] = f'new{_step}'
        _idx.value = _t
        cheap_write(items=_sitems, index=_idx, input=_swritten[_t])
    for _bad in (-1, 30, 55):
        _idx.value = _bad
        cheap_write(items=_sitems, index=_idx, input='nope')

    def check_staged_strings(
        _items: list[PlayerStat] = _sitems,
        _w: tuple[tuple[int, str], ...] = tuple(_swritten.items()),
    ) -> None:
        _wd = dict(_w)
        for i, s in enumerate(_items):
            got = str(ctx.get(s))
            want = _wd.get(i, '%var.player/sv3%' if i == 7 else f'word{i}')
            assert got == want, (i, got, want)

    ctx.assert_all(check_staged_strings)


with ExecutionContext(ignore_action_limits=True) as ctx:
    _ditems = [PlayerStat(f'dv{i}').as_double() for i in range(30)]
    for _i, _s in enumerate(_ditems):
        ctx.put(_s, _i + 0.5, ignore_warning=True)
    _idx = PlayerStat('idx').as_long()
    _idx.value = 17
    cheap_write(items=_ditems, index=_idx, input=-2.25)

    def check_staged_doubles(_items: list[PlayerStat] = _ditems) -> None:
        for i, s in enumerate(_items):
            got = float(ctx.get_raw(s))
            want = -2.25 if i == 17 else i + 0.5
            assert abs(got - want) < 0.001, (i, got, want)

    ctx.assert_all(check_staged_doubles)


with ExecutionContext(ignore_action_limits=True) as ctx:
    _mitems = [
        (PlayerStat(f'mv{2 * i}').as_long(), PlayerStat(f'mv{2 * i + 1}').as_string())
        for i in range(15)
    ]
    for _i, (_a, _b) in enumerate(_mitems):
        ctx.put(_a, 1000 + _i, ignore_warning=True)
        ctx.put(_b, f's{_i}', ignore_warning=True)
    _idx = PlayerStat('idx').as_long()
    _idx.value = 9
    cheap_write(items=_mitems, index=_idx, input=(4242, 'hit'))

    def check_staged_mixed(_items: list = _mitems) -> None:
        for i, (a, b) in enumerate(_items):
            got = (int(ctx.get(a)), str(ctx.get(b)))
            want = (4242, 'hit') if i == 9 else (1000 + i, f's{i}')
            assert got == want, (i, got, want)

    ctx.assert_all(check_staged_mixed)
