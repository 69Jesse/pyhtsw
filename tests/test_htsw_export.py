import json
import tempfile
from pathlib import Path

from pyhtsw import (
    NPC,
    Container,
    chat,
    create_event,
    create_function,
    create_item,
    create_menu,
    create_npc,
    create_region,
    give_item,
    set_projects_folder,
)

tmp = Path(tempfile.mkdtemp())
set_projects_folder(tmp, save=False)

with Container() as container:
    wand = create_item('blaze_rod', name='&aMagic Wand')

    @wand.right_click
    def on_right() -> None:
        chat('used the wand')

    border = create_item('black_stained_glass_pane', name=' ', importable_name='Border')

    shop = create_menu('Shop', 6)
    shop.place(border, x=0)
    shop.place(border, xy_check=lambda x, y: (x + y) % 2 == 0)

    @shop.on(item=wand, x=3, y=4)
    def buy() -> None:
        chat('bought')

    spawn = create_region('Spawn', ((0, 100, 0), (10, 110, 10)))

    @spawn.on_enter
    def enter() -> None:
        chat('entered')

    merchant = create_npc(
        'Merchant',
        (1, 64, 2),
        skin='Steve',
        look_at_players=True,
        equipment=NPC.Equipment(hand=wand),
    )

    @merchant.right_click
    def right() -> None:
        chat('hello')

    @create_function('Tick', repeat_ticks=20, icon=wand)
    def tick() -> None:
        chat('tick')

    @create_event('Player Join')
    def join() -> None:
        give_item(wand)


container.export('Export Test')

root = tmp / 'export-test'
data = json.loads((root / 'import.json').read_text())

# functions
assert data['functions'][0]['name'] == 'Tick'
assert data['functions'][0]['repeatTicks'] == 20
assert data['functions'][0]['icon'] == {'item': 'minecraft:blaze_rod'}
assert data['functions'][0]['actions'] == 'functions/tick.htsl'
assert (root / 'functions' / 'tick.htsl').exists()

# events
assert data['events'][0] == {
    'event': 'Player Join',
    'actions': 'events/player-join.htsl',
}
# the declared item is referenced by name from the action
assert 'giveItem "Magic Wand"' in (root / 'events' / 'player-join.htsl').read_text()

# items: a declared item becomes an items[] entry, named after its display name
items = {entry['name']: entry for entry in data['items']}
assert items['Magic Wand']['nbt'] == 'items/magic-wand.snbt'
assert items['Magic Wand']['rightClickActions'] == 'items/magic-wand/right.htsl'
assert 'leftClickActions' not in items['Magic Wand']
assert 'rightClickActions' not in items['Border']

# region
region = data['regions'][0]
assert region['name'] == 'Spawn'
assert region['bounds'] == {
    'from': {'x': 0, 'y': 100, 'z': 0},
    'to': {'x': 10, 'y': 110, 'z': 10},
}
assert region['onEnterActions'] == 'regions/spawn/enter.htsl'

# npc
npc = data['npcs'][0]
assert npc['name'] == 'Merchant'
assert npc['pos'] == {'x': 1, 'y': 64, 'z': 2}
assert npc['skin'] == 'Steve'
assert npc['lookAtPlayers'] is True
assert npc['equipment'] == {'hand': 'items/magic-wand.snbt'}

# menu: x=0 fills the whole top row, the checkerboard fills (x+y) even cells,
# and the explicit (3, 4) -> slot 31 overrides whatever was there.
menu = data['menus'][0]
assert menu['size'] == 6
slots = {entry['slot']: entry for entry in menu['slots']}
assert set(range(9)).issubset(slots)  # row 0 fully filled
assert slots[31]['nbt'] == 'items/magic-wand.snbt'
assert slots[31]['actions'] == 'menus/shop/slot-3-4.htsl'
assert slots[10]['nbt'] == 'items/border.snbt'  # (1,1) -> checkerboard

# pretty snbt is indented
snbt = (root / 'items' / 'magic-wand.snbt').read_text()
assert '\n    id: "minecraft:blaze_rod"' in snbt
