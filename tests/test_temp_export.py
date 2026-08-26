import re
import tempfile
from pathlib import Path

from pyhtsw import (
    Container,
    PlayerStat,
    TemporaryStat,
    chat,
    function,
    set_projects_folder,
)

tmp = Path(tempfile.mkdtemp())
set_projects_folder(tmp, save=False)


with Container() as container:

    @function('Foo')
    def foo() -> None:
        held = TemporaryStat().with_value(123)
        x = PlayerStat('x')
        y = PlayerStat('y')
        z = PlayerStat('z')
        # Two computed augmented assigns -> per-statement transient temps that
        # must not reuse the held temp's tmp<n>.
        x.value += y + z
        z.value += z + x
        chat(f'{held}')


container.export('Temp Export')

htsl = (tmp / 'temp-export' / 'functions' / 'foo.htsl').read_text(encoding='utf-8')
lines = htsl.splitlines()

# The held temp is the one assigned the literal 123.
held_line = next(ln for ln in lines if ln.endswith('= 123 false'))
held_match = re.search(r'"(tmp\d+)"', held_line)
assert held_match is not None, held_line
held_name = held_match.group(1)

# The chat at the end must read that exact temp ...
chat_line = next(ln for ln in lines if ln.startswith('chat '))
assert held_name in chat_line, (held_name, chat_line, htsl)

# ... and nothing may overwrite the held temp between its assignment and the read
# (the bug: a transient `tmp0 = %var.player/y%` stomped `tmp0 = 123`).
overwrites = [
    ln
    for ln in lines
    if ln.startswith(f'var "{held_name}" =') and not ln.endswith('= 123 false')
]
assert not overwrites, (held_name, overwrites, htsl)

# The transient temps for `y + z` / `z + x` must use a different name.
transient_lines = [
    ln for ln in lines if '%var.player/y%' in ln or '%var.player/x%' in ln
]
assert all(f'"{held_name}"' not in ln for ln in transient_lines), (held_name, htsl)
