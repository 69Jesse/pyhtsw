import io
from contextlib import redirect_stdout

from pyhtsw import EmulatedHouse, PlayerStat

# Plain text
buf = io.StringIO()
with redirect_stdout(buf):
    with EmulatedHouse() as house:
        house.print('hello')

output = buf.getvalue()
assert 'hello' in output, output


# Stat reference is substituted with the put value
buf = io.StringIO()
with redirect_stdout(buf):
    with EmulatedHouse() as house:
        x = PlayerStat('x').as_long()
        house.put(x, 42)
        house.print('value:', x)

output = buf.getvalue()
assert 'value:' in output, output
assert '42' in output, output


# Multiple prints all show up
buf = io.StringIO()
with redirect_stdout(buf):
    with EmulatedHouse() as house:
        house.print('first')
        house.print('second')
        house.print('third')

output = buf.getvalue()
assert 'first' in output, output
assert 'second' in output, output
assert 'third' in output, output
# In order
assert output.index('first') < output.index('second') < output.index('third')


# Computed values are printed after the writes finish
buf = io.StringIO()
with redirect_stdout(buf):
    with EmulatedHouse() as house:
        x = PlayerStat('x').as_long()
        y = PlayerStat('y').as_long()
        house.put(x, 10)
        y.value = x + 5
        house.print('y =', y)

output = buf.getvalue()
assert '15' in output, output
