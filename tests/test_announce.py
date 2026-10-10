import json
import tempfile
from enum import Enum
from pathlib import Path

from helpers import expect_exception

import pyhtsw.compiler.lock as lock
from pyhtsw import (
    Container,
    EmulatedHouse,
    GlobalStat,
    IfAll,
    PlayerStat,
    chat,
    function,
)
from pyhtsw.expression.condition.conditional_expression import ConditionalExpression
from pyhtsw.ext import Announcer, Num, Text


class Reason(Enum):
    JOIN = 0
    LEAVE = 1


def flatten(expressions: list[object]) -> list[object]:
    out: list[object] = []
    for expression in expressions:
        out.append(expression)
        if isinstance(expression, ConditionalExpression):
            out.extend(flatten(list(expression.if_expressions)))
            out.extend(flatten(list(expression.else_expressions)))
    return out


def conditionals(expressions: list[object]) -> int:
    return sum(1 for e in flatten(expressions) if isinstance(e, ConditionalExpression))


# === The enqueue is conditional-free, so it may sit inside an IfAll ===

with Container() as container:
    announcer = Announcer('Ann', capacity=6, prefix='qa')

    @announcer.format
    def joined(reason: Reason, name: Text) -> None:
        chat(f'{name} {reason.name}')

    @announcer.format
    def streak(name: Text, amount: Num, iota: Num) -> None:
        chat(f'{name} {amount} {iota}')

    gate = PlayerStat('gate').as_long()
    who = PlayerStat('who').as_string()

    @function('Caller')
    def caller() -> None:
        with IfAll(gate > 0):
            joined.announce(reason=Reason.JOIN, name=who)

    @function('Pump', repeat_ticks=5)
    def pump() -> None:
        announcer.tick()


caller_block = next(b for b in container.blocks if b.get_name() == 'Caller')
inner = flatten(list(caller_block.expressions))
# One conditional: the caller's own gate. The enqueue adds none.
assert conditionals(list(caller_block.expressions)) == 1, inner
# Two text columns are never needed here, so the row is one string plus one
# packed long: 5 shifts x 2 + 1 text write + 1 pack + 1 counter.
assert announcer.text_slots == 1
assert announcer.enqueue_actions == 5 * 2 + 1 + 5 + 1

pump_block = next(b for b in container.blocks if b.get_name() == 'Pump')
# Stale drop, overflow clamp, drain.
assert conditionals(list(pump_block.expressions)) == 3


# === Formats and specializations get distinct ids ===

ids = {
    specialization.title(): specialization.id
    for specialization in announcer._specializations
}
assert ids == {'Joined JOIN': 1, 'Joined LEAVE': 2, 'Streak': 3}, ids


# === Packing round-trips through the queue ===


def drain_once(ann: Announcer) -> None:
    """The drain, without the cooldown gate or the trigger."""
    ann._index.value = ann._counter
    ann._index.value -= 1
    from pyhtsw.ext.array_read_write import array_read

    assert ann._rows is not None
    array_read(
        items=ann._rows,
        index=ann._index,
        output=[*ann._current_text, ann._current_packed],
    )
    ann._counter.value -= 1


with EmulatedHouse(ignore_action_limits=True) as house:
    ann = Announcer('Ann2', capacity=4, prefix='qb')

    seen: list[tuple[int, int]] = []

    @ann.format(ranges={'amount': (0, 4000), 'iota': (-50, 50)})
    def numbers(amount: Num, iota: Num) -> None:
        chat(f'{amount}/{iota}')

    @ann.format
    def plain(name: Text) -> None:
        chat(f'{name}')

    name_stat = PlayerStat('nm').as_string()
    house.put(name_stat, 'Notch', ignore_warning=True)

    # Three rows in, FIFO out.
    numbers.announce(amount=1, iota=-50)  # type: ignore[arg-type]
    numbers.announce(amount=4000, iota=50)  # type: ignore[arg-type]
    plain.announce(name=name_stat)

    out_amount = GlobalStat('oam').as_long().with_auto_unset(False)
    out_iota = GlobalStat('oio').as_long().with_auto_unset(False)

    def check_first() -> None:
        assert int(house.get_raw(ann._counter)) == 3

    house.assert_all(check_first)

    for expected in ((1, -50), (4000, 50)):
        drain_once(ann)
        field_amount, field_iota = ann._formats[0].num_fields
        unpacked_amount = ann._unpack(field_amount)
        unpacked_iota = ann._unpack(field_iota)
        out_amount.value = unpacked_amount
        out_iota.value = unpacked_iota

        def check(_expected: tuple[int, int] = expected) -> None:
            assert (
                int(house.get_raw(out_amount)),
                int(house.get_raw(out_iota)),
            ) == _expected, (
                house.get_raw(out_amount),
                house.get_raw(out_iota),
                _expected,
            )

        house.assert_all(check)

    # The oldest row is the string one, and its id names the second format.
    drain_once(ann)

    def check_string() -> None:
        assert str(house.get_raw(ann._current_text[0])) == 'Notch'
        packed = int(house.get_raw(ann._current_packed))
        assert (
            packed & ((1 << ann._id_bits) - 1) == ann._formats[1].specializations[0].id
        ), packed

    house.assert_all(check_string)


# === Overflow drops the oldest and the counter is clamped ===

with EmulatedHouse(ignore_action_limits=True) as house:
    ann = Announcer('Ann3', capacity=2, prefix='qc')

    @ann.format
    def tick_message(value: Num) -> None:
        chat(f'{value}')

    for value in (10, 20, 30):
        tick_message.announce(value=value)  # type: ignore[arg-type]

    out = GlobalStat('ovl').as_long().with_auto_unset(False)
    field = ann._formats[0].num_fields[0]

    ann._counter.value = 2  # what the pump's clamp would leave behind
    drain_once(ann)
    out.value = ann._unpack(field)

    def check_dropped() -> None:
        # 10 fell off the end; 20 is now the oldest.
        assert int(house.get_raw(out)) == 20, house.get_raw(out)

    house.assert_all(check_dropped)


# === A queue nobody ticked for stale_ms is dropped; a live one is kept ===

with EmulatedHouse(ignore_action_limits=True) as house:
    ann = Announcer('Ann7', capacity=4, prefix='qg')

    @ann.format
    def left(value: Num) -> None:
        chat(f'{value}')

    # Stranded rows from an emptied house: the last tick is long gone.
    left.announce(value=1)  # type: ignore[arg-type]
    left.announce(value=2)  # type: ignore[arg-type]
    ann._last_tick.value = 0
    ann.on_join()

    def check_dropped_stale() -> None:
        assert int(house.get_raw(ann._counter)) == 0, house.get_raw(ann._counter)

    house.assert_all(check_dropped_stale)

    # The drop stamped the tick, so a row queued right after survives it.
    left.announce(value=3)  # type: ignore[arg-type]
    ann._emit_drop_stale()

    def check_kept_live() -> None:
        assert int(house.get_raw(ann._counter)) == 1, house.get_raw(ann._counter)

    house.assert_all(check_kept_live)


with expect_exception(ValueError):
    Announcer('Ann8', prefix='qh', stale_ms=500)


# === A misused call site fails at build time ===

with Container():
    ann = Announcer('Ann4', prefix='qd')

    @ann.format
    def two_fields(name: Text, amount: Num) -> None:
        chat(f'{name} {amount}')

    with expect_exception(TypeError):
        two_fields.announce(name='x')  # type: ignore[call-arg]

    with expect_exception(TypeError):
        two_fields.announce(name='x', amount=1, extra=2)  # type: ignore[call-arg]

    @ann.format(ranges={'amount': (0, 10)})
    def bounded(amount: Num) -> None:
        chat(f'{amount}')

    with expect_exception(ValueError):
        bounded.announce(amount=11)  # type: ignore[arg-type]


# === An unannotated or unenumerable parameter is rejected ===

with Container():
    ann = Announcer('Ann5', prefix='qe')

    with expect_exception(TypeError):

        @ann.format
        def bad(value) -> None:  # noqa: ARG001
            chat('x')

    with expect_exception(TypeError):

        @ann.format
        def worse(text: str) -> None:  # noqa: ARG001
            chat('x')


# === A body may nest, and stays inside the one dispatcher ===

with Container() as container:
    ann = Announcer('Ann6', prefix='qf')

    @ann.format(ranges={'amount': (0, 100)})
    def complicated(amount: Num) -> None:
        with IfAll(amount > 5):
            chat('big')
            with IfAll(amount > 50):
                chat('huge')
        chat('done')

    @function('Pump6', repeat_ticks=5)
    def pump6() -> None:
        ann.tick()


names = {block.get_name() for block in container.blocks}
assert 'Ann6' in names and not any(n.startswith('Ann6:') for n in names), names

dispatch_block = next(b for b in container.blocks if b.get_name() == 'Ann6')
flat = flatten(list(dispatch_block.expressions))
assert not any(
    isinstance(e, ConditionalExpression)
    for parent in flat
    if isinstance(parent, ConditionalExpression)
    for e in (*parent.if_expressions, *parent.else_expressions)
), 'the dispatcher must not contain a nested conditional'
# The format's `chat('done')` run plus its two nested runs.
assert conditionals(list(dispatch_block.expressions)) == 3

# === Ids are pinned in the lock, so a new format is appended, not inserted ===

with tempfile.TemporaryDirectory() as tmp:
    lock_path = Path(tmp) / 'pyhtsw.lock'

    def build(run: int, titles: list[str]) -> list[tuple[str, int]]:
        lock._LOCKS.clear()
        with Container(lock_file=lock_path, projects_folder=tmp) as built:
            pinned = Announcer('Pinned', prefix='qp')
            for title in titles:
                pinned.format(name=title)(lambda: chat('x'))

            @function('Pinned Pump', repeat_ticks=5)
            def pinned_pump() -> None:
                pinned.tick()

        built.export(f'pinned-{run}')
        return [(s.title(), s.id) for s in pinned._specializations]

    assert build(1, ['Alpha', 'Beta']) == [('Alpha', 1), ('Beta', 2)]
    order = build(2, ['Gamma', 'Alpha', 'Beta'])
    assert order == [('Alpha', 1), ('Beta', 2), ('Gamma', 3)], order
    # A format no longer declared keeps its id reserved.
    assert build(3, ['Beta', 'Delta']) == [('Beta', 2), ('Delta', 4)]
    assert json.loads(lock_path.read_text(encoding='utf-8')) == {
        'version': 1,
        'announcer': {'Pinned': {'Alpha': 1, 'Beta': 2, 'Gamma': 3, 'Delta': 4}},
    }

    with expect_exception(ValueError), Container(lock_file=None):
        twins = Announcer('Twins', prefix='qt')
        twins.format(name='Same')(lambda: chat('a'))
        twins.format(name='Same')(lambda: chat('b'))
        twins.tick()


# === The dispatcher belongs to the announcer's module, not the first format's ===

with Container() as container:
    owned = Announcer('Owned', prefix='qo')
    exec(
        "@owned.format\ndef elsewhere() -> None:\n    chat('x')\n",
        {'__name__': 'other.module', 'owned': owned, 'chat': chat},
    )

owner = container.find_importable('functions', 'Owned')
assert owner is not None and owner.module == __name__, owner


print('test_announce OK')
