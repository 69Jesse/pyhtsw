import json
import tempfile
from pathlib import Path

from pyhtsw import (
    Container,
    IfAll,
    WithinRegion,
    chat,
    create_region,
    set_projects_folder,
)

tmp = Path(tempfile.mkdtemp())
set_projects_folder(tmp, save=False)


with Container() as container:
    # Handlers up front...
    arena = create_region(
        'Arena',
        ((0, 60, 0), (16, 80, 16)),
        on_enter=lambda: chat('&centered the arena'),
        on_exit=lambda: chat('&cleft the arena'),
    )

    # ...or attached afterwards, which is what a loop needs.
    lobby = create_region('Lobby')

    @lobby.on_enter
    def _welcome() -> None:
        chat('&awelcome')

    @lobby.on_exit
    def _bye() -> None:
        chat('&7bye')

    # Bounds are optional at declaration and settable after it - htsw imports a
    # region without them and you place it in-game.
    assert lobby.bounds is None
    lobby.corners((10, 70, 10), (0, 60, 0))
    assert lobby.bounds == ((0, 60, 0), (10, 70, 10)), lobby.bounds

    # A region built in a loop, the thing the subclass form could not do.
    pads = [create_region(f'Pad {n}', ((n, 60, 0), (n + 1, 61, 1))) for n in range(3)]
    for pad in pads:
        pad.attach('enter', lambda: chat('&bpad'))

    # The condition takes the value, or a bare name for a region declared
    # in-game.
    @create_region('Watcher').on_enter
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
    create_region('Twin')
    raised = False
    try:
        create_region('Twin')
    except RuntimeError:
        raised = True
    assert raised, 'expected a duplicate region name to be refused'
