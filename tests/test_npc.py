from helpers import expect_exception

from pyhtsw import NPC, Container, GlobalStat, Item, chat, create_npc

flag = GlobalStat('flag').as_long()


def _entry(container: Container, name: str) -> dict:
    npc = container.find_importable('npcs', name)
    assert npc is not None, name
    return {
        'left': npc.left,  # type: ignore[attr-defined]
        'right': npc.right,  # type: ignore[attr-defined]
        'redirect': npc.left_click_redirect,  # type: ignore[attr-defined]
        'skin': npc.skin,  # type: ignore[attr-defined]
        'pos': npc.pos,  # type: ignore[attr-defined]
    }


with Container() as container:
    create_npc(
        'Guard',
        (1, 2, 3),
        on_left_click=lambda: chat('left'),
        on_right_click=lambda: chat('right'),
        skin='Alex',
        look_at_players=True,
    )

guard = _entry(container, 'Guard')
assert guard['left'] is not None and guard['right'] is not None
assert guard['redirect'] is None
assert guard['skin'] == 'Alex'
assert guard['pos'] == (1, 2, 3)


with Container() as container:
    smith = create_npc('Smith', (0, 0, 0))

    @smith.left_click
    def _smith_left() -> None:
        chat('clang')

    @smith.right_click
    def _smith_right() -> None:
        chat('what do you want')


smith_entry = _entry(container, 'Smith')
assert smith_entry['left'] is not None and smith_entry['right'] is not None


with Container() as container:
    create_npc('Statue', (5, 5, 5), hide_name_tag=True)

statue = _entry(container, 'Statue')
assert statue['left'] is None and statue['right'] is None


with Container() as container:
    create_npc('Shopkeeper', (2, 2, 2), on_click=lambda: chat('welcome'))

shop = _entry(container, 'Shopkeeper')
assert shop['right'] is not None, shop
assert shop['left'] is None, shop
assert shop['redirect'] is True, shop


with Container() as container:
    banker = create_npc('Banker', (3, 3, 3))

    @banker.click
    def _bank() -> None:
        chat('deposit')


bank = _entry(container, 'Banker')
assert bank['right'] is not None and bank['left'] is None
assert bank['redirect'] is True


for kwargs in (
    {'on_left_click': lambda: chat('x')},
    {'on_right_click': lambda: chat('x')},
    {'left_click_redirect': False},
):
    with expect_exception(ValueError):
        with Container():
            create_npc('Clash', (0, 0, 0), on_click=lambda: chat('y'), **kwargs)  # type: ignore[arg-type]


with expect_exception(ValueError):
    with Container():
        npc = create_npc('Late', (0, 0, 0), on_left_click=lambda: chat('x'))
        npc.attach('both', lambda: chat('y'))

with expect_exception(ValueError):
    with Container():
        npc = create_npc('Early', (0, 0, 0), on_click=lambda: chat('y'))
        npc.attach('left', lambda: chat('x'))


with expect_exception(ValueError):
    with Container():
        broken = create_npc('Broken', (0, 0, 0), left_click_redirect=False)

        @broken.click
        def _both() -> None:
            chat('nope')


with Container() as container:
    helmet = Item('diamond_helmet')

    def _greet(npc: NPC) -> None:
        chat(f'I am {npc.name}')

    create_npc(
        'Knight',
        (7, 7, 7),
        on_click=_greet,
        equipment=NPC.Equipment(helmet=helmet),
    )

knight = _entry(container, 'Knight')
assert knight['right'] is not None

# A one-argument handler receives the NPC it belongs to, so it can read its own
# name and position rather than having them closed over at every call site.
htsl = knight['right'].into_htsl()
assert 'I am Knight' in htsl, htsl
