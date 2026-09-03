from pyhtsw import (
    EmulatedHouse,
    EmulatedPlayer,
    GlobalStat,
    IfAll,
    PlayerStat,
    disable_global_export,
    exit_function,
    function,
    trigger_function,
)
from pyhtsw.placeholders.player import PlayerName

disable_global_export()


# A `var` (player stat) is stored per-player; the same key on two players holds
# two independent values.
with EmulatedHouse(players=['A', 'B']) as house:
    a, b = house.players
    x = PlayerStat('x').as_long()
    a.put(x, 10)
    b.put(x, 20)

assert int(a.get_raw(x)) == 10, a.get_raw(x)
assert int(b.get_raw(x)) == 20, b.get_raw(x)


# A `globalvar` is shared: writing it as one player is visible to every player
# and to the context.
with EmulatedHouse(players=['A', 'B']) as house:
    a, b = house.players
    g = GlobalStat('shared').as_long()
    a.put(g, 7)

assert int(b.get_raw(g)) == 7, b.get_raw(g)
assert int(house.get_raw(g)) == 7, house.get_raw(g)


# Each player's name resolves `%player.name%` to themselves.
with EmulatedHouse(players=['Alice', 'Bob']) as house:
    alice, bob = house.players

assert str(alice.get(PlayerName)) == 'Alice', alice.get(PlayerName)
assert str(bob.get(PlayerName)) == 'Bob', bob.get(PlayerName)


# `players=N` makes N auto-named players; `add_player` appends more.
with EmulatedHouse(players=3) as house:
    assert len(house.players) == 3, len(house.players)
    extra = house.add_player('late')
    assert house.players[-1] is extra
    assert len(house.players) == 4, len(house.players)


# No players given → exactly one default player, which `house.put`/`house.get`
# (current_player) route through, preserving single-player behavior.
with EmulatedHouse() as house:
    assert len(house.players) == 1, len(house.players)
    x = PlayerStat('x').as_long()
    house.put(x, 99)

assert int(house.get(x)) == 99, house.get(x)


# `trigger_function(..., True)` runs the function once per player; a plain
# `trigger_function(...)` runs it only for the current player.
with EmulatedHouse(players=['A', 'B', 'C']) as house:
    a, b, c = house.players
    house.current_player = a
    counter = GlobalStat('counter').as_long()
    touched = PlayerStat('touched').as_long()
    house.put(counter, 0, ignore_warning=True)

    @function('bump')
    def bump() -> None:
        counter.value += 1
        touched.value = 1

    trigger_function(bump, True)  # once per player → 3 runs

assert int(house.get_raw(counter)) == 3, house.get_raw(counter)
assert int(a.get_raw(touched)) == 1, a.get_raw(touched)
assert int(b.get_raw(touched)) == 1, b.get_raw(touched)
assert int(c.get_raw(touched)) == 1, c.get_raw(touched)


# A function that fans *itself* out runs "for everyone but the caster": the
# caster's own entry call puts the function on its 4-tick cooldown, so the
# inner `… true` skips them. This is the raycast's core mechanism.
with EmulatedHouse(players=['A', 'B', 'C']) as house:
    a, b, c = house.players
    house.current_player = a
    active = GlobalStat('active').as_long()
    visited = PlayerStat('visited').as_long()
    house.put(active, 0, ignore_warning=True)

    holder: dict[str, object] = {}

    @function('spread')
    def spread() -> None:
        with IfAll(active == 0):
            active.value = 1
            trigger_function(holder['fn'], True)  # type: ignore[arg-type]
            exit_function()
        visited.value = 1

    holder['fn'] = spread
    trigger_function(spread)  # A is the caster / origin

assert int(a.get_raw(visited)) == 0, a.get_raw(visited)  # caster excluded
assert int(b.get_raw(visited)) == 1, b.get_raw(visited)
assert int(c.get_raw(visited)) == 1, c.get_raw(visited)


# Passing pre-built EmulatedPlayer objects works, and `.put` on them is usable
# before any expression is written.
p1 = EmulatedPlayer('p1')
p2 = EmulatedPlayer('p2')
with EmulatedHouse(players=[p1, p2]) as house:
    score = PlayerStat('score').as_long()
    p1.put(score, 5)
    p2.put(score, 8)

assert int(p1.get_raw(score)) == 5, p1.get_raw(score)
assert int(p2.get_raw(score)) == 8, p2.get_raw(score)
