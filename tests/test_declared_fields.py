from pyhtsw import (
    NPC,
    Command,
    Container,
    Event,
    Function,
    Group,
    Item,
    Menu,
    Region,
    Team,
    chat,
    command,
    event,
    function,
)

with Container():
    vip = Group(
        'VIP',
        tag='VIP',
        tag_shown_in_chat=True,
        color='Gold',
        priority=5,
        allow=['Fly'],
        deny=['Ban'],
        chat_speed='Slow 1s',
        default_gamemode='ADVENTURE',
    )
    red = Team('Red', tag='RED', color='Dark Red', friendly_fire=False)

    assert vip.priority == 5, vip.priority
    assert vip.tag == 'VIP'
    assert vip.tag_shown_in_chat is True
    assert vip.color == 'Gold'
    assert vip.chat_speed == 'Slow 1s'
    assert vip.default_gamemode == 'ADVENTURE'
    assert vip.permissions == {'Fly': True, 'Ban': False}, vip.permissions

    assert red.tag == 'RED'
    assert red.color == 'Dark Red'
    assert red.friendly_fire is False

    # Declared, but the field was left out: None, not an error.
    plain = Group('Plain')
    assert plain.priority is None
    assert plain.permissions is None

    # The returned mapping is a view, not the registered dict.
    raised = False
    try:
        vip.permissions['Fly'] = False  # type: ignore[index]
    except TypeError:
        raised = True
    assert raised, 'expected permissions to be read-only'
    assert vip.permissions == {'Fly': True, 'Ban': False}

    # Declaring the same name twice is a hard error, not a silent merge.
    raised = False
    try:
        Group('VIP')
    except RuntimeError as error:
        raised = True
        assert 'VIP' in str(error), error
    assert raised, 'expected a RuntimeError for a duplicate group declaration'

    raised = False
    try:
        Team('Red')
    except RuntimeError as error:
        raised = True
        assert 'Red' in str(error), error
    assert raised, 'expected a RuntimeError for a duplicate team declaration'


with Container() as container:
    wand = Item('blaze_rod', name='&aWand', importable_name='Wand')
    shop = Menu('Shop', 6)
    smith = NPC('Smith', (1, 64, 2), skin='Steve', look_at_players=True)
    spawn = Region('Spawn', ((0, 100, 0), (10, 110, 10)))
    squad = Team('Squad', tag='SQ')
    mods = Group('Mods', priority=9)

    @function('Tick', repeat_ticks=20, icon=wand)
    def tick() -> None:
        chat('tick')

    @command('warp', mode='Self', required_priority=3, listed=True)
    def warp() -> None:
        chat('warp')

    @event('Player Join')
    def join() -> None:
        chat('hi')

    # Each factory returns the value type, not a class or a raw callback.
    assert isinstance(wand, Item)
    assert isinstance(shop, Menu)
    assert isinstance(smith, NPC)
    assert isinstance(spawn, Region)
    assert isinstance(squad, Team)
    assert isinstance(mods, Group)
    assert isinstance(tick, Function)
    assert isinstance(warp, Command)
    assert isinstance(join, Event)

    # ...and every one of them answers for its own declaration.
    assert shop.name == 'Shop' and shop.size == 6
    assert smith.name == 'Smith' and smith.pos == (1, 64, 2)
    assert smith.skin == 'Steve' and smith.look_at_players is True
    assert smith.hide_name_tag is None
    assert spawn.name == 'Spawn'
    assert spawn.bounds == ((0, 100, 0), (10, 110, 10))
    assert tick.name == 'Tick' and tick.repeat_ticks == 20
    assert tick.icon is wand
    assert warp.name == 'warp' and warp.mode == 'Self'
    assert warp.required_priority == 3 and warp.listed is True
    assert join.name == 'Player Join' and join.event == 'Player Join'
    assert wand.importable.name == 'Wand'
    assert wand.key == 'blaze_rod' and wand.name == '&aWand'

    # `.importable` is the declaration itself, for every kind.
    assert shop.importable is container.find_importable('menus', 'Shop')
    assert join.importable is container.find_importable('events', 'Player Join')

    smith.pos = (9.0, 65.0, 9.0)
    smith.hide_name_tag = True
    spawn.bounds = ((1, 1, 1), (2, 2, 2))
    mods.priority = 11
    tick.repeat_ticks = 40

    assert smith.pos == (9.0, 65.0, 9.0) and smith.hide_name_tag is True
    assert spawn.bounds == ((1, 1, 1), (2, 2, 2))
    assert mods.priority == 11
    assert tick.repeat_ticks == 40

    # `corners` normalises either order into a low/high pair.
    spawn.corners((10, 70, 10), (0, 60, 4))
    assert spawn.bounds == ((0, 60, 4), (10, 70, 10)), spawn.bounds

    # Renaming keeps the container's name index in step.
    spawn.name = 'Lobby'
    assert spawn.name == 'Lobby'
    assert container.find_importable('regions', 'Lobby') is spawn.importable
    assert container.find_importable('regions', 'Spawn') is None

    # A name another importable of the same kind already holds is refused, and
    # nothing moved; a name only another *kind* holds is fine.
    admins = Group('Admins')
    mods.name = 'Squad'  # a team, not a group -> free
    assert mods.name == 'Squad'
    raised = False
    try:
        mods.name = 'Admins'
    except RuntimeError:
        raised = True
    assert raised, 'expected a duplicate rename to be refused'
    assert mods.name == 'Squad'
    assert container.find_importable('groups', 'Admins') is admins.importable

    # A read-only field says so rather than silently dropping the write.
    raised = False
    try:
        mods.permissions = {}  # type: ignore[assignment]
    except AttributeError:
        raised = True
    assert raised, 'expected permissions to reject assignment'


with Container() as container:
    first = Item(
        'blaze_rod',
        name='&aRecord',
        importable_name='Record1',
        on_right_click=lambda: chat('one'),
    )
    second = Item(
        'blaze_rod',
        name='&aRecord',
        importable_name='Record2',
        on_right_click=lambda: chat('two'),
    )

    names = [i.identifier() for i in container.importables if i.kind == 'items']
    assert names == ['Record1', 'Record2'], names
    assert first.importable.name == 'Record1'
    assert second.importable.name == 'Record2'
    # An explicit name never aliases a byte-identical twin - that is the whole
    # point of asking for one.
    assert first.importable is not second.importable

    # Without a name, an interactive item derives one from its display name.
    derived = Item('stick', name='&eTorch', on_click=lambda: chat('lit'))
    assert derived.importable.name == 'Torch', derived.importable.name
