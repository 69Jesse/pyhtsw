from pyhtsw import Container, Group, Team, create_group, create_team

with Container():
    vip = create_group(
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
    red = create_team('Red', tag='RED', color='Dark Red', friendly_fire=False)

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

    # A bare reference compares equal to the declared value, so it reads the
    # same fields.
    assert Group('VIP') == vip
    assert Group('VIP').priority == 5
    assert Team('Red').color == 'Dark Red'

    # Declared, but the field was left out: None, not an error.
    plain = create_group('Plain')
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

    # Never declared anywhere: a raise, not a silent None.
    raised = False
    try:
        _ = Group('Ghost').priority
    except RuntimeError as error:
        raised = True
        assert 'create_group' in str(error), error
    assert raised, 'expected a RuntimeError for an undeclared group'

    raised = False
    try:
        _ = Team('Ghost').color
    except RuntimeError as error:
        raised = True
        assert 'create_team' in str(error), error
    assert raised, 'expected a RuntimeError for an undeclared team'


# A group declared in another container is not this container's group.
with Container():
    raised = False
    try:
        _ = Group('VIP').priority
    except RuntimeError:
        raised = True
    assert raised, 'expected the declaration lookup to be per-container'

    # The object create_group handed out still knows its own declaration.
    assert vip.priority == 5
