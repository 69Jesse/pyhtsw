# Emulation

`EmulatedHouse` runs expressions **in Python** instead of emitting HTSL —
useful for testing and debugging logic without importing into a real house.

```python
from pyhtsw import EmulatedHouse, PlayerStat

coins = PlayerStat('coins')

with EmulatedHouse() as house:
    house.put(coins, 50, ignore_warning=True)
    coins.value += 100

    def check() -> None:
        assert int(house.get(coins)) == 150

    house.assert_all(check)
```

- `house.put(stat, value, ignore_warning=True)` seeds a value.
- `house.get(stat)` reads via the HTSL placeholder path; `house.get_raw(stat)` reads
  the exact backend value.
- `house.assert_all(...)` / `house.assert_any(...)` take conditions or plain
  callables that run `assert` checks.
- `EmulatedHouse(players=3)` or `players=[EmulatedPlayer('alice'), ...]` gives
  the house more than one player; `house.using_player(p)` switches who runs.
- Everything runs at `__exit__`.

The emulated house follows Java arithmetic semantics (64-bit long wraparound,
truncating integer division, UTF-16 string lengths) so what it computes is what
the real house would compute.
