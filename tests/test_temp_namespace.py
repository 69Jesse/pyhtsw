import io
import re
from contextlib import redirect_stdout

from pyhtsw import (
    Container,
    EmulatedHouse,
    IfAll,
    PlayerStat,
    TemporaryStat,
    chat,
)


def temp_numbers(htsl: str) -> set[int]:
    return {int(m) for m in re.findall(r'tmp(\d+)', htsl)}


with Container() as container:
    tmp0 = PlayerStat('tmp0').as_long()
    tmp1 = PlayerStat('tmp1').as_long()
    somestatx = PlayerStat('somestatx').as_long()
    tmp0.value = 123
    tmp1.value += somestatx + 456
    chat(f'{tmp0}')

htsl = container.into_htsl()
# The anonymous temp for `somestatx + 456` must not reuse tmp0 or tmp1.
assert 'var "tmp0" = "%var.player/somestatx' not in htsl, htsl
assert htsl.splitlines()[0] == 'var "tmp0" = 123 true', htsl
assert htsl.splitlines()[-1] == 'chat "%var.player/tmp0 0%"', htsl


# Same thing, executed: chat must read 123, not somestatx + 456.
with EmulatedHouse() as house:
    tmp0 = PlayerStat('tmp0').as_long()
    tmp1 = PlayerStat('tmp1').as_long()
    somestatx = PlayerStat('somestatx').as_long()
    house.put(somestatx, 1000, ignore_warning=True)
    house.put(tmp1, 0, ignore_warning=True)
    tmp0.value = 123
    tmp1.value += somestatx + 456

    def check_tmp0(_t=tmp0) -> None:
        assert int(house.get_raw(_t)) == 123, int(house.get_raw(_t))

    house.assert_all(check_tmp0)


with Container() as container:
    held = [PlayerStat(f'tmp{i}').as_long() for i in range(5)]
    x = PlayerStat('x').as_long()
    y = PlayerStat('y').as_long()
    for i, stat in enumerate(held):
        stat.value = i
    out = PlayerStat('out').as_long()
    out.value = (x + y) * (x - y)  # needs two anonymous temps
    chat(f'{held[0]} {held[3]}')

htsl = container.into_htsl()
used = temp_numbers(htsl)
# The five consumer temps appear; the computed temps must not have taken 0..4.
assert {0, 1, 2, 3, 4} <= used, used
computed_lines = [ln for ln in htsl.splitlines() if 'x 0%' in ln or 'y 0%' in ln]
assert all(not re.search(r'"tmp[0-4]"', ln) for ln in computed_lines), htsl


with EmulatedHouse() as house:
    tmp0 = PlayerStat('tmp0').as_long()
    cond = PlayerStat('cond').as_long()
    a = PlayerStat('a').as_long()
    b = PlayerStat('b').as_long()
    house.put(cond, 1, ignore_warning=True)
    house.put(a, 7, ignore_warning=True)
    house.put(b, 3, ignore_warning=True)
    tmp0.value = 999
    with IfAll(cond == 1):
        # a computed temp inside the body must not clobber the outer tmp0
        b.value = a + b + 100

    def check_outer(_t=tmp0) -> None:
        assert int(house.get_raw(_t)) == 999, int(house.get_raw(_t))

    house.assert_all(check_outer)


with Container() as container:
    a = PlayerStat('a').as_long()
    t = TemporaryStat().as_long()
    t.value = a
    t.value += 100
    chat(f'{t}')

htsl = container.into_htsl()
assert 'tmp1000001' not in htsl, htsl  # raw pre-rename number must never leak
assert htsl.splitlines()[-1] == 'chat "%var.player/tmp0 0%"', htsl
write_lines = [ln for ln in htsl.splitlines() if ln.startswith('var "tmp')]
assert all('"tmp0"' in ln for ln in write_lines), htsl  # all writes hit tmp0 too


# Executed: the f-string read sees the written value.
buf = io.StringIO()
with redirect_stdout(buf):
    with EmulatedHouse() as house:
        a = PlayerStat('a').as_long()
        t = TemporaryStat().as_long()
        house.put(a, 5, ignore_warning=True)
        t.value = a
        t.value += 100
        chat(f'{t}')
assert '105' in buf.getvalue(), buf.getvalue()


with Container() as container:
    tmp0 = PlayerStat('tmp0').as_long()
    a = PlayerStat('a').as_long()
    b = PlayerStat('b').as_long()
    t = TemporaryStat().as_long()
    u = TemporaryStat().as_long()
    tmp0.value = 42
    t.value = a + b  # held + a transient temp for the sum
    u.value = a - b
    chat(f'{tmp0} {t} {u}')

htsl = container.into_htsl()
assert htsl.splitlines()[0] == 'var "tmp0" = 42 true', htsl
# The three reads in the chat must be three distinct names.
last = htsl.splitlines()[-1]
names = re.findall(r'tmp\d+', last)
assert len(names) == 3 and len(set(names)) == 3, last


# A typeless held temp can be created and typed lazily, like any stat.
with EmulatedHouse() as house:
    x = PlayerStat('x').as_long()
    scratch = TemporaryStat()  # no type yet
    house.put(x, -9, ignore_warning=True)
    scratch.as_long().value = abs(x)

    def check_abs(_s=scratch) -> None:
        assert int(house.get_raw(_s.as_long())) == 9, int(house.get_raw(_s.as_long()))

    house.assert_all(check_abs)
