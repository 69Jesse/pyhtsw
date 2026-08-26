from pyhtsw import (
    Item,
    chat,
    create_event,
    create_function,
    create_item,
    create_menu,
    create_npc,
    create_region,
    display_menu,
    give_item,
)

wand = create_item(
    'blaze_rod',
    name='&aMagic Wand',
    lore='&7Right-click me',
)


@wand.right_click
def on_right() -> None:
    chat('&dPoof!')


border = Item('black_stained_glass_pane', name=' ')

shop = create_menu('Magic Shop', 6)
# decoration: fill the top row, then a checkerboard
shop.place(border, x=0)
shop.place(border, xy_check=lambda x, y: (x + y) % 2 == 0)


@shop.on(item=wand, x=2, y=4)
def buy_wand() -> None:
    give_item(wand)
    chat('&aYou bought the Magic Wand!')


spawn = create_region('Spawn', ((0, 100, 0), (16, 120, 16)))


@spawn.on_enter
def enter() -> None:
    chat('&aWelcome to spawn!')


create_npc(
    '&aShopkeeper',
    (8, 100, 8),
    skin='Alex',
    look_at_players=True,
    on_right_click=lambda: display_menu(shop),
)


@create_event('Player Join')
def on_join() -> None:
    give_item(wand)
    chat('&eWelcome! Right-click the wand or visit the shopkeeper.')


@create_function('Heartbeat', repeat_ticks=200, icon=wand)
def heartbeat() -> None:
    chat('&8The house hums quietly...')
