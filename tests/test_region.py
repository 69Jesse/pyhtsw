import json
import tempfile
from pathlib import Path

from pyhtsw import (
    Container,
    IfAll,
    Region,
    WithinRegion,
    chat,
)

tmp = Path(tempfile.mkdtemp())

with Container(projects_folder=tmp) as container:
    # Handlers up front...
    arena = Region(
        'Arena',
        ((0, 60, 0), (16, 80, 16)),
        on_enter=lambda: chat('&centered the arena'),
        on_exit=lambda: chat('&cleft the arena'),
    )

    # ...or attached afterwards, which is what a loop needs.
    lobby = Region('Lobby', ((0, 0, 0), (1, 1, 1)))

    @lobby.on_enter
    def _welcome() -> None:
        chat('&awelcome')

    @lobby.on_exit
    def _bye() -> None:
        chat('&7bye')

    # Bounds are settable after declaration, which is what `corners` is for.
    lobby.corners((10, 70, 10), (0, 60, 0))
    assert lobby.bounds == ((0, 60, 0), (10, 70, 10)), lobby.bounds

    # A region built in a loop, the thing the subclass form could not do.
    pads = [Region(f'Pad {n}', ((n, 60, 0), (n + 1, 61, 1))) for n in range(3)]
    for pad in pads:
        pad.attach('enter', lambda: chat('&bpad'))

    # The condition takes the value, or a bare name for a region declared
    # in-game.
    @Region('Watcher', ((0, 0, 0), (1, 1, 1))).on_enter
    def _watch() -> None:
        with IfAll(WithinRegion(arena)):
            chat('&ealso in the arena')
        with IfAll(WithinRegion('Hand Placed')):
            chat('&ein a region pyhtsw never declared')


container.export('Region Test')
root = tmp / 'region-test'
data = json.loads((root / 'import.json').read_text())
regions = {entry['name']: entry for entry in data['regions']}

assert set(regions) == {
    'Arena',
    'Lobby',
    'Pad 0',
    'Pad 1',
    'Pad 2',
    'Watcher',
}, set(regions)

assert regions['Arena']['bounds'] == {
    'from': {'x': 0, 'y': 60, 'z': 0},
    'to': {'x': 16, 'y': 80, 'z': 16},
}
assert regions['Arena']['onEnterActions'] == 'regions/arena/enter.htsl'
assert regions['Arena']['onExitActions'] == 'regions/arena/exit.htsl'
assert 'entered the arena' in (root / 'regions' / 'arena' / 'enter.htsl').read_text()
assert 'left the arena' in (root / 'regions' / 'arena' / 'exit.htsl').read_text()

# Bounds set after declaration still reach import.json.
assert regions['Lobby']['bounds'] == {
    'from': {'x': 0, 'y': 60, 'z': 0},
    'to': {'x': 10, 'y': 70, 'z': 10},
}
assert 'welcome' in (root / 'regions' / 'lobby' / 'enter.htsl').read_text()
assert 'bye' in (root / 'regions' / 'lobby' / 'exit.htsl').read_text()

watcher = (root / 'regions' / 'watcher' / 'enter.htsl').read_text()
assert 'inRegion "Arena"' in watcher, watcher
assert 'inRegion "Hand Placed"' in watcher, watcher


# Two regions cannot share a name.
with Container():
    Region('Twin', ((0, 0, 0), (1, 1, 1)))
    raised = False
    try:
        Region('Twin', ((0, 0, 0), (1, 1, 1)))
    except RuntimeError:
        raised = True
    assert raised, 'expected a duplicate region name to be refused'


# htsw's schemaSpec.ts marks bounds required, so a region cannot be declared
# here and placed in-game later. Omitting them is a TypeError at the call...
with Container():
    raised = False
    try:
        Region('Unbounded')  # type: ignore[call-arg]
    except TypeError:
        raised = True
    assert raised, 'expected a region without bounds to be refused'

# ...and clearing them afterwards is caught at build, before htsw sees it.
with tempfile.TemporaryDirectory() as unbounded_tmp:
    with Container(projects_folder=unbounded_tmp) as unbounded:
        cleared = Region('Cleared', ((0, 0, 0), (1, 1, 1)))
        cleared.bounds = None  # type: ignore[assignment]

    raised = False
    try:
        unbounded.export('Unbounded Test')
    except ValueError as error:
        raised = 'has no bounds' in str(error)
    assert raised, 'expected a bounds-less region to fail at build'
