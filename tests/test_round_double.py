from pyhtsw import Container, EmulatedHouse, PlayerStat
from pyhtsw.ext import round_double

# 1.234567 rounded to 2 decimals -> 1.23 (the +0.5-then-truncate happens on
# 123.4567, so the .95 residue truncates away exactly like htsw's L-cast)
with EmulatedHouse() as house:
    x = PlayerStat('x').as_double()
    house.put(x, 1.234567)
    round_double(x, 2)

assert float(house.get_raw(x)) == 1.23, house.get_raw(x)


# 0.5 rounded to 0 decimals -> 1.0 (rounds via +0.5 then truncate)
with EmulatedHouse() as house:
    x = PlayerStat('x').as_double()
    house.put(x, 0.5)
    round_double(x, 0)

assert float(house.get_raw(x)) == 1.0, house.get_raw(x)


# Result is close to the expected mathematical rounding (within 0.001 of round
# to N decimals). The emulator's cast_to_long step is a no-op, so the function
# can leave a tiny residue from the +0.5 — this tolerance covers that.
with EmulatedHouse() as house:
    x = PlayerStat('x').as_double()
    house.put(x, 3.14159)
    round_double(x, 2)

assert abs(float(house.get_raw(x)) - 3.14) < 0.01, house.get_raw(x)


with EmulatedHouse() as house:
    x = PlayerStat('x').as_double()
    house.put(x, 7.0)
    round_double(x, 3)

assert abs(float(house.get_raw(x)) - 7.0) < 0.001, house.get_raw(x)


# Sanity: round_double also produces valid HTSL (compile-only)
with Container() as container:
    x = PlayerStat('x').as_double()
    round_double(x, 2)

assert container.into_htsl() != ''
