import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from helpers import expect_exception  # noqa: E402

from pyhtsw import (
    Container,
    Item,
    Menu,
    chat,
    display_menu,
    set_projects_folder,
)

tmp = Path(tempfile.mkdtemp())
set_projects_folder(tmp, save=False)


Black = Item('black_stained_glass_pane', name=' ')
Gray = Item('gray_stained_glass_pane', name=' ')
Wand = Item('blaze_rod', name='&aWand')


def build_page(title: str, greeting: str) -> Menu:
    """The point of the whole API: one function, called in a loop, and the
    handler closes over `greeting` without a default-argument dance."""
    menu = Menu(title, 6)
    menu.fill(Black, xy_check=lambda x, y: menu.distance_from_edge(x, y) == 0)
    menu.fill(Gray, xy_check=lambda x, y: menu.distance_from_edge(x, y) == 1)
    menu.place(Wand, slot=4)

    @menu.on(item=Wand, slot=22)
    def _greet() -> None:
        chat(greeting)

    return menu


with Container() as container:
    pages = [build_page(f'Page {i}', f'hello {i}') for i in range(3)]

    nav_menu = Menu('Nav', 3)

    @nav_menu.on(item=Wand, slot=[10, 12, 14])
    def _nav() -> None:
        display_menu(pages[0])

    legacy = Menu('Legacy', 3)
    legacy.place(Black, xy_check=lambda x, y: x == 0)

    @legacy.on(item=Wand, slot=13)
    def buy() -> None:
        chat('bought')

    @legacy.on(item=Gray, slot=[18, 26])
    def corners() -> None:
        chat('corner')


container.export('Menu Builder Test')

root = tmp / 'menu-builder-test'
data = json.loads((root / 'import.json').read_text(encoding='utf-8'))
menus = {menu['name']: menu for menu in data['menus']}

assert set(menus) == {'Page 0', 'Page 1', 'Page 2', 'Nav', 'Legacy'}, sorted(menus)

page = menus['Page 1']
assert page['size'] == 6
slots = {entry['slot']: entry for entry in page['slots']}

# Ring 0 is black, ring 1 is gray, the middle is untouched.
assert 'gray' not in slots[0]['nbt'] and 'black' in slots[0]['nbt']
assert 'gray' in slots[10]['nbt']
assert 20 not in slots, 'ring 2 should be left empty'

# `place` and `fill` write no actions; `on` does.
assert 'actions' not in slots[4], slots[4]
assert 'actions' not in slots[0], slots[0]
assert 'actions' in slots[22], slots[22]

# slot=4 landed at row 0, column 4 — the flat index, not x=4.
assert slots[4]['nbt'] == slots[22]['nbt'], 'both are the wand'

# Each page closed over its own greeting.
actions = {}
for index in range(3):
    entry = {slot['slot']: slot for slot in menus[f'Page {index}']['slots']}[22]
    actions[index] = (root / entry['actions']).read_text(encoding='utf-8')
assert 'hello 0' in actions[0] and 'hello 1' in actions[1] and 'hello 2' in actions[2]
assert 'hello 1' not in actions[0]

nav = {entry['slot']: entry for entry in menus['Nav']['slots']}
assert sorted(nav) == [10, 12, 14], sorted(nav)
assert all('actions' in entry for entry in nav.values())

legacy = {entry['slot']: entry for entry in menus['Legacy']['slots']}
assert sorted(legacy) == [0, 1, 2, 3, 4, 5, 6, 7, 8, 13, 18, 26], sorted(legacy)
assert 'actions' in legacy[13] and 'actions' not in legacy[0]
assert 'actions' in legacy[18] and 'actions' in legacy[26]

with expect_exception(ValueError):
    Menu('Bad Size', 7)  # type: ignore[arg-type]

with expect_exception(ValueError):
    Menu('Both', 3).place(Wand, slot=1, x=0)

with expect_exception(ValueError):
    Menu('Out Of Range', 1).place(Wand, slot=[99])

print('PASS')
