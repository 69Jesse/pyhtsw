from helpers import expect_exception

from pyhtsw import EmulatedHouse, GlobalStat, PlayerStat
from pyhtsw.ext.vector import Vector


def make(capacity: int = 4) -> Vector:
    return Vector(
        holders=[
            (GlobalStat(f'n{i}').as_string(), GlobalStat(f'a{i}').as_long())
            for i in range(capacity)
        ],
        counter=GlobalStat('c').as_long(),
        on_overflow='override_oldest',
    )


# take_first pulls the first match and closes the gap, leaving the rest in order.
with EmulatedHouse(ignore_action_limits=True) as house:
    v = make()
    name = PlayerStat('on').as_string()
    action = PlayerStat('oa').as_long()
    hit = PlayerStat('hit').as_long()
    v.push(('alice', 1))
    v.push(('bob', 2))
    v.push(('carol', 3))
    v.take_first(
        where=lambda n, _a: n == 'bob',
        output=(name, action),
        if_present=lambda: hit.__setattr__('value', 1),
    )

    def check_take() -> None:
        assert house.get_raw(name) == 'bob'
        assert int(house.get_raw(action)) == 2
        assert int(house.get_raw(hit)) == 1
        assert int(house.get_raw(v.counter)) == 2
        assert house.get_raw(v.holders[0][0]) == 'alice'
        assert house.get_raw(v.holders[1][0]) == 'carol'

    house.assert_all(check_take)


# A miss leaves everything alone and runs if_absent.
with EmulatedHouse(ignore_action_limits=True) as house:
    v = make()
    name = PlayerStat('on').as_string()
    action = PlayerStat('oa').as_long()
    missed = PlayerStat('missed').as_long()
    v.push(('alice', 1))
    v.take_first(
        where=lambda n, _a: n == 'zed',
        output=(name, action),
        if_absent=lambda: missed.__setattr__('value', 1),
    )

    def check_miss() -> None:
        assert int(house.get_raw(missed)) == 1
        assert int(house.get_raw(v.counter)) == 1
        assert house.get_raw(v.holders[0][0]) == 'alice'

    house.assert_all(check_miss)


# A stale slot past the counter is never matched, and only the first of two
# equal entries goes.
with EmulatedHouse(ignore_action_limits=True) as house:
    v = make()
    name = PlayerStat('on').as_string()
    action = PlayerStat('oa').as_long()
    v.push(('dup', 1))
    v.push(('dup', 2))
    v.take_first(where=lambda n, _a: n == 'dup', output=(name, action))
    v.take_first(where=lambda n, _a: n == 'dup', output=(name, action))
    v.take_first(where=lambda n, _a: n == 'dup', output=(name, action))

    def check_dup() -> None:
        assert int(house.get_raw(action)) == 2
        assert int(house.get_raw(v.counter)) == 0

    house.assert_all(check_dup)


# Full: the oldest entry makes room.
with EmulatedHouse(ignore_action_limits=True) as house:
    v = make(capacity=2)
    name = PlayerStat('on').as_string()
    action = PlayerStat('oa').as_long()
    v.push(('one', 1))
    v.push(('two', 2))
    v.push(('three', 3))
    v.take_first(where=lambda n, _a: n == 'one', output=(name, action))

    def check_overflow() -> None:
        assert int(house.get_raw(v.counter)) == 2
        assert house.get_raw(v.holders[0][0]) == 'two'
        assert house.get_raw(v.holders[1][0]) == 'three'

    house.assert_all(check_overflow)


# A gated push only lands when its condition holds.
with EmulatedHouse(ignore_action_limits=True) as house:
    v = make(capacity=2)
    gate = PlayerStat('gate').as_long()
    v.push(('one', 1))
    v.push(('two', 2), when=(gate == 1,))
    gate.value = 1
    v.push(('three', 3), when=(gate == 1,))
    v.push(('four', 4), when=(gate == 1,))

    def check_gate() -> None:
        assert int(house.get_raw(v.counter)) == 2
        assert house.get_raw(v.holders[0][0]) == 'three'
        assert house.get_raw(v.holders[1][0]) == 'four'

    house.assert_all(check_gate)


# A take that could not fit one branch is refused up front.
with expect_exception(ValueError):
    big = make(capacity=12)
    with EmulatedHouse(ignore_action_limits=True):
        big.take_first(
            where=lambda n, _a: n == 'x',
            output=(PlayerStat('on').as_string(), PlayerStat('oa').as_long()),
        )
