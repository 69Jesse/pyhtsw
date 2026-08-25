import json
import sys
import tempfile
from pathlib import Path

from pyhtsw import (
    Container,
    Item,
    chat,
    create_function,
    give_item,
    set_projects_folder,
)

tmp = Path(tempfile.mkdtemp())
set_projects_folder(tmp, save=False)


def use() -> None:
    chat('used')


with Container() as container:
    WAND = Item('blaze_rod', name='&dWand', on_right_click=use)
    STACK = WAND.cloned(count=3)  # still a wand, three of them
    SAME = WAND.cloned(count=1)  # byte-identical: the same wand
    ICON = WAND.cloned(lore='&7Cost: 5', on_click=None)  # a shop icon
    OWNER_MENU = Item.housing_menu()
    GUEST_MENU = Item.housing_menu('GUEST')

    @create_function('Hand Them Out')
    def hand_them_out() -> None:
        for item in (WAND, STACK, SAME, ICON, OWNER_MENU, GUEST_MENU):
            give_item(item)


container.export('Item Copies')
root = tmp / 'item-copies'
data = json.loads((root / 'import.json').read_text(encoding='utf-8'))
items = {entry['name']: entry for entry in data['items']}

assert 'Wand' in items, sorted(items)
assert 'Wand x3' in items, sorted(items)
assert 'rightClickActions' in items['Wand'], items['Wand']
assert 'rightClickActions' in items['Wand x3'], items['Wand x3']

assert SAME._importable_name == 'Wand', SAME._importable_name
assert STACK._importable_name == 'Wand x3', STACK._importable_name

assert ICON._importable_name is None
inert = [
    name
    for name, entry in items.items()
    if name.startswith('Wand') and 'rightClickActions' not in entry
]
assert len(inert) == 1, sorted(items)

bodies = [
    (root / entry['nbt']).read_text(encoding='utf-8')
    for name, entry in items.items()
    if name.startswith('Housing Menu')
]
assert len(bodies) == 2, sorted(items)

owner = next(b for b in bodies if 'OWNER' in b)
assert 'minecraft:nether_star' in owner, owner
assert 'HideFlags: 255' in owner, owner
assert 'HOUSING_MENU: "OWNER"' in owner, owner
assert '§dHousing Menu§7 (Right Click)' in owner, owner

guest = next(b for b in bodies if 'GUEST' in b)
assert 'minecraft:dark_oak_door' in guest, guest
assert 'HOUSING_MENU: "GUEST"' in guest, guest

assert Item.from_snbt(owner).into_snbt() == Item.housing_menu().into_snbt()

print('PASS')
sys.exit(0)
