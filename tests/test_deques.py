from collections import deque

from helpers import expect_exception

from pyhtsw import Container, EmulatedHouse, PlayerStat
from pyhtsw.expression.condition.conditional_expression import ConditionalExpression
from pyhtsw.ext.stack_queue import Deque, IntDeque

# === IntDeque: the four operations ===

# push_back then pop_front is FIFO; push_front then pop_front is LIFO.
with EmulatedHouse(ignore_action_limits=True) as house:
    d = IntDeque(
        holder=PlayerStat('h').as_long(),
        counter=PlayerStat('c').as_long(),
        most=255,
    )
    out = PlayerStat('out').as_long()
    d.push_back(1)
    d.push_back(2)
    d.pop_front(output=out)

    def check_fifo() -> None:
        assert int(house.get(out)) == 1

    house.assert_all(check_fifo)


with EmulatedHouse(ignore_action_limits=True) as house:
    d = IntDeque(
        holder=PlayerStat('h').as_long(),
        counter=PlayerStat('c').as_long(),
        most=255,
    )
    out = PlayerStat('out').as_long()
    d.push_front(1)
    d.push_front(2)
    d.pop_front(output=out)

    def check_lifo() -> None:
        assert int(house.get(out)) == 2

    house.assert_all(check_lifo)


# pop_back takes the far end whichever way the values went in.
for _pusher in ('push_front', 'push_back'):
    with EmulatedHouse(ignore_action_limits=True) as house:
        d = IntDeque(
            holder=PlayerStat('h').as_long(),
            counter=PlayerStat('c').as_long(),
            most=255,
        )
        out = PlayerStat('out').as_long()
        for _v in (1, 2, 3):
            getattr(d, _pusher)(_v)
        d.pop_back(output=out)
        _expected = 1 if _pusher == 'push_front' else 3

        def check_pop_back(_e: int = _expected, _o=out) -> None:
            assert int(house.get(_o)) == _e

        house.assert_all(check_pop_back)


# === IntDeque against a real deque ===

SCRIPT: list[tuple[str, int]] = [
    ('push_back', 3),
    ('push_front', 7),
    ('push_back', 11),
    ('pop_back', 0),
    ('push_front', 5),
    ('push_front', 9),
    ('pop_front', 0),
    ('push_back', 2),
    ('pop_back', 0),
    ('pop_front', 0),
    ('pop_back', 0),
    ('pop_front', 0),
    ('pop_front', 0),
    ('push_back', 6),
    ('pop_back', 0),
]

for _most, _capacity in ((255, None), (255, 16), (1023, 12)):
    model: deque[int] = deque()
    limit = (64 // _most.bit_length()) if _capacity is None else _capacity
    expected_pops: list[int] = []
    for _op, _v in SCRIPT:
        if _op == 'push_back':
            if len(model) < limit:
                model.append(_v)
        elif _op == 'push_front':
            if len(model) < limit:
                model.appendleft(_v)
        elif _op == 'pop_back':
            expected_pops.append(model.pop() if model else -1)
        else:
            expected_pops.append(model.popleft() if model else -1)

    with EmulatedHouse(ignore_action_limits=True) as house:
        d = IntDeque(
            holder=lambda i: PlayerStat(f'h{i}').as_long(),
            counter=PlayerStat('c').as_long(),
            most=_most,
            capacity=_capacity,
        )
        outs = [PlayerStat(f'o{i}').as_long() for i in range(len(expected_pops))]
        taken = 0
        for _op, _v in SCRIPT:
            if _op in ('push_back', 'push_front'):
                getattr(d, _op)(_v)
            else:
                getattr(d, _op)(output=outs[taken])
                taken += 1

        def check_script(_o: list = outs, _e: list = expected_pops) -> None:
            assert [int(house.get(s)) for s in _o] == _e, (
                [int(house.get(s)) for s in _o],
                _e,
            )

        house.assert_all(check_script)


# A popped slot is cleared, so a later push_back does not OR into stale bits.
with EmulatedHouse(ignore_action_limits=True) as house:
    d = IntDeque(
        holder=PlayerStat('h').as_long(),
        counter=PlayerStat('c').as_long(),
        most=255,
    )
    a, b = PlayerStat('a').as_long(), PlayerStat('b').as_long()
    d.push_back(255)
    d.pop_back(output=a)
    d.push_back(1)
    d.pop_back(output=b)

    def check_cleared() -> None:
        assert int(house.get(a)) == 255
        assert int(house.get(b)) == 1

    house.assert_all(check_cleared)


# The same, across a holder boundary.
with EmulatedHouse(ignore_action_limits=True) as house:
    d = IntDeque(
        holder=lambda i: PlayerStat(f'h{i}').as_long(),
        counter=PlayerStat('c').as_long(),
        most=255,
        capacity=16,
    )
    out = PlayerStat('out').as_long()
    for _ in range(9):
        d.push_back(255)
    d.pop_back(output=out)
    d.push_back(4)
    d.pop_back(output=out)

    def check_cross_holder() -> None:
        assert int(house.get(out)) == 4

    house.assert_all(check_cross_holder)


# Popping an empty deque writes the if_empty default.
with EmulatedHouse(ignore_action_limits=True) as house:
    d = IntDeque(
        holder=PlayerStat('h').as_long(),
        counter=PlayerStat('c').as_long(),
        most=255,
    )
    out = PlayerStat('out').as_long()
    d.pop_back(output=out)

    def check_empty_back() -> None:
        assert int(house.get(out)) == -1

    house.assert_all(check_empty_back)


# === IntDeque overflow policies ===


# most=255 -> 8 bits -> a single holder is full at 8 values.
def full_deque(policy: str) -> IntDeque:
    d = IntDeque(
        holder=PlayerStat('h').as_long(),
        counter=PlayerStat('c').as_long(),
        most=255,
        on_overflow=policy,  # type: ignore[arg-type]
    )
    for v in range(1, 9):
        d.push_back(v)
    return d


# push_front on a full deque with override_oldest drops the back.
with EmulatedHouse(ignore_action_limits=True) as house:
    d = full_deque('override_oldest')
    outs = [PlayerStat(f'o{i}').as_long() for i in range(8)]
    d.push_front(9)
    for _i in range(8):
        d.pop_front(output=outs[_i])

    def check_front_override() -> None:
        assert [int(house.get(s)) for s in outs] == [9, 1, 2, 3, 4, 5, 6, 7]

    house.assert_all(check_front_override)


# push_back on a full deque with override_oldest drops the front.
with EmulatedHouse(ignore_action_limits=True) as house:
    d = full_deque('override_oldest')
    outs = [PlayerStat(f'o{i}').as_long() for i in range(8)]
    d.push_back(9)
    for _i in range(8):
        d.pop_front(output=outs[_i])

    def check_back_override() -> None:
        assert [int(house.get(s)) for s in outs] == [2, 3, 4, 5, 6, 7, 8, 9]

    house.assert_all(check_back_override)


# override_newest overwrites the pushing end instead of evicting anything.
with EmulatedHouse(ignore_action_limits=True) as house:
    d = full_deque('override_newest')
    outs = [PlayerStat(f'o{i}').as_long() for i in range(8)]
    d.push_back(9)
    for _i in range(8):
        d.pop_front(output=outs[_i])

    def check_newest_back() -> None:
        assert [int(house.get(s)) for s in outs] == [1, 2, 3, 4, 5, 6, 7, 9]

    house.assert_all(check_newest_back)


with EmulatedHouse(ignore_action_limits=True) as house:
    d = full_deque('override_newest')
    outs = [PlayerStat(f'o{i}').as_long() for i in range(8)]
    d.push_front(9)
    for _i in range(8):
        d.pop_front(output=outs[_i])

    def check_newest_front() -> None:
        assert [int(house.get(s)) for s in outs] == [9, 2, 3, 4, 5, 6, 7, 8]

    house.assert_all(check_newest_front)


# override_oldest needs a capacity that fills its holders exactly.
with expect_exception(ValueError):
    IntDeque(
        holder=PlayerStat('h').as_long(),
        counter=PlayerStat('c').as_long(),
        most=255,
        capacity=5,
        capacity_is_exact=True,
        on_overflow='override_oldest',
    )


# === Deque (slot-based) ===

# Strings survive all four operations.
with EmulatedHouse(ignore_action_limits=True) as house:
    d = Deque(
        holders=[PlayerStat(f's{i}').as_string() for i in range(4)],
        counter=PlayerStat('c').as_long(),
        if_empty='EMPTY',
    )
    ra, rb, rc = (PlayerStat(n).as_string() for n in ('ra', 'rb', 'rc'))
    d.push_back('mid')
    d.push_front('first')
    d.push_back('last')
    d.pop_front(output=ra)
    d.pop_back(output=rb)
    d.pop_back(output=rc)

    def check_strings() -> None:
        assert str(house.get_raw(ra)) == 'first'
        assert str(house.get_raw(rb)) == 'last'
        assert str(house.get_raw(rc)) == 'mid'

    house.assert_all(check_strings)


# Slot-based, against the same oracle. Long slots take array_read's fast path
# for pop_back; string slots take the cascade, so both shapes are covered.
for _typed in ('long', 'string'):
    _cast = str if _typed == 'string' else int
    model = deque()
    limit = 6
    expected_pops = []
    for _op, _v in SCRIPT:
        if _op == 'push_back':
            if len(model) < limit:
                model.append(_v)
        elif _op == 'push_front':
            if len(model) < limit:
                model.appendleft(_v)
        elif _op == 'pop_back':
            expected_pops.append(model.pop() if model else -1)
        else:
            expected_pops.append(model.popleft() if model else -1)

    with EmulatedHouse(ignore_action_limits=True) as house:
        if _typed == 'long':
            slots = [PlayerStat(f'q{i}').as_long() for i in range(limit)]
            outs = [PlayerStat(f'o{i}').as_long() for i in range(len(expected_pops))]
        else:
            slots = [PlayerStat(f'q{i}').as_string() for i in range(limit)]
            outs = [PlayerStat(f'o{i}').as_string() for i in range(len(expected_pops))]
        d = Deque(
            holders=slots,
            counter=PlayerStat('c').as_long(),
            if_empty=_cast(-1),
        )
        taken = 0
        for _op, _v in SCRIPT:
            if _op in ('push_back', 'push_front'):
                getattr(d, _op)(_cast(_v))
            else:
                getattr(d, _op)(output=outs[taken])
                taken += 1

        def check_slot_script(
            _o: list = outs,
            _e: list = expected_pops,
            _c=_cast,
        ) -> None:
            got = [_c(house.get_raw(s)) for s in _o]
            assert got == [_c(v) for v in _e], (got, _e)

        house.assert_all(check_slot_script)


# Width > 1: every column travels together.
with EmulatedHouse(ignore_action_limits=True) as house:
    d = Deque(
        holders=[
            (PlayerStat(f'n{i}').as_string(), PlayerStat(f'v{i}').as_long())
            for i in range(3)
        ],
        counter=PlayerStat('c').as_long(),
    )
    name, value = PlayerStat('rn').as_string(), PlayerStat('rv').as_long()
    d.push_back(('alpha', 1))
    d.push_front(('beta', 2))
    d.pop_back(output=(name, value))

    def check_width() -> None:
        assert str(house.get_raw(name)) == 'alpha'
        assert int(house.get(value)) == 1

    house.assert_all(check_width)


# A duplicated slot stat is rejected, as for Stack/Queue.
with expect_exception(ValueError):
    Deque(
        holders=[PlayerStat('dup').as_long(), PlayerStat('dup').as_long()],
        counter=PlayerStat('c').as_long(),
    )


# === Cost ===
#
# Measured behind a full action list, so the fixer realizes its wrappers.
def measure(build) -> int:
    with Container(ignore_action_limits=True) as container:
        for _ in range(25):
            PlayerStat('fill1').value += PlayerStat('fill2')
        build()
    return container.expression_counts()[ConditionalExpression]


def int_deque() -> IntDeque:
    return IntDeque(
        holder=PlayerStat('h').as_long(),
        counter=PlayerStat('c').as_long(),
        most=255,
    )


# Every IntDeque operation stays within a couple of conditionals on one holder.
for _op, _kwargs in (
    ('push_front', {'value': 1}),
    ('push_back', {'value': 1}),
    ('pop_front', {'output': PlayerStat('o').as_long()}),
    ('pop_back', {'output': PlayerStat('o').as_long()}),
):
    _cost = measure(lambda o=_op, k=_kwargs: getattr(int_deque(), o)(**k))
    assert _cost <= 4, (_op, _cost)
