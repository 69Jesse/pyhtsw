import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pyhtsw
from pyhtsw import (
    NPC,
    Container,
    Item,
    Menu,
    Region,
    chat,
    event,
    function,
    give_item,
    set_projects_folder,
)

tmp = Path(tempfile.mkdtemp())
set_projects_folder(tmp, save=False)


# Define every importable kind in a throwaway container (so nothing lands in the
# global one); the handles below carry their importable for `export` to find.
with Container():
    wand = Item('blaze_rod', name='&aMagic Wand')

    @wand.right_click
    def on_right() -> None:
        chat('used the wand')

    border = Item('black_stained_glass_pane', name=' ', importable_name='Border')

    shop = Menu('Shop', 6)
    shop.place(border, x=0)

    @shop.on(item=wand, x=3, y=4)
    def buy() -> None:
        chat('bought')

    spawn = Region('Spawn', ((0, 100, 0), (10, 110, 10)))

    @spawn.on_enter
    def enter() -> None:
        chat('entered')

    merchant = NPC(
        'Merchant',
        (1, 64, 2),
        skin='Steve',
        look_at_players=True,
    )

    @merchant.right_click
    def right() -> None:
        chat('hello')

    @function('Tick', repeat_ticks=20, icon=wand)
    def tick() -> None:
        chat('tick')

    @event('Player Join')
    def join() -> None:
        give_item(wand)


# A module-like namespace; `tick`/`join` are listed twice to prove dedup.
module = SimpleNamespace(
    wand=wand,
    border=border,
    shop=shop,
    spawn=spawn,
    merchant=merchant,
    tick=tick,
    join=join,
    tick_again=tick,
)
pyhtsw.export(module, 'Module Export')

root = tmp / 'module-export'
data = json.loads((root / 'import.json').read_text())

# every kind made it across
assert {fn['name'] for fn in data['functions']} == {'Tick'}
assert {ev['event'] for ev in data['events']} == {'Player Join'}
assert {it['name'] for it in data['items']} == {'Magic Wand', 'Border'}
assert {rg['name'] for rg in data['regions']} == {'Spawn'}
assert {mn['name'] for mn in data['menus']} == {'Shop'}
assert {np['name'] for np in data['npcs']} == {'Merchant'}

# function metadata is preserved and the action body is re-run (not empty)
fn = data['functions'][0]
assert fn['repeatTicks'] == 20
assert fn['icon'] == {'item': 'minecraft:blaze_rod'}
assert 'chat "tick"' in (root / 'functions' / 'tick.htsl').read_text()

# event body too
assert 'giveItem "Magic Wand"' in (root / 'events' / 'player-join.htsl').read_text()

# item / region / npc / menu click bodies survived the re-run
assert 'used the wand' in (root / 'items' / 'magic-wand' / 'right.htsl').read_text()
assert 'entered' in (root / 'regions' / 'spawn' / 'enter.htsl').read_text()
assert 'hello' in (root / 'npcs' / 'merchant' / 'right.htsl').read_text()
assert 'bought' in (root / 'menus' / 'shop' / 'slot-3-4.htsl').read_text()


# A single handle and a bare list both work; a bare build callback is run.
with Container():

    @function('Solo')
    def solo() -> None:
        chat('solo')


def build_extra() -> None:
    chat('built by callback')


pyhtsw.export([solo, build_extra], 'List Export')
list_data = json.loads((tmp / 'list-export' / 'import.json').read_text())
names = {fn['name'] for fn in list_data['functions']}
assert names == {'Solo', 'List Export'}, names  # callback wrapped under project name
assert (
    'built by callback'
    in (tmp / 'list-export' / 'functions' / 'list-export.htsl').read_text()
)


# Nothing exportable -> a clear error.
raised = False
try:
    pyhtsw.export(SimpleNamespace(), 'Empty Export')
except ValueError:
    raised = True
assert raised, 'expected a ValueError when there is nothing to export'
