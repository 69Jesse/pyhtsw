import json
import tempfile
from pathlib import Path

from pyhtsw import (
    Container,
    change_player_group,
    chat,
    create_command,
    create_group,
    create_npc,
    create_team,
    set_player_team,
    set_projects_folder,
)

tmp = Path(tempfile.mkdtemp())
set_projects_folder(tmp, save=False)


# A declared team is the same Team value the actions already take.
with Container() as container:
    red = create_team('Red', tag='RED', color='Dark Red', friendly_fire=False)
    vip = create_group(
        'VIP',
        tag='VIP',
        tag_shown_in_chat=True,
        color='Gold',
        priority=5,
        allow=['Fly', 'Build', '/tp'],
        deny=['Ban'],
        chat_speed='Slow 1s',
        default_gamemode='ADVENTURE',
    )

    @create_command('warp', mode='Self', required_priority=3, listed=True)
    def _warp() -> None:
        set_player_team(red)
        change_player_group(vip)

    greeter = create_npc(
        '&aGreeter',
        (1, 2, 3),
        left_click_redirect=True,
        look_at_players=True,
        skin='Alex',
    )

    @greeter.right_click
    def _hi() -> None:
        chat('&ahello')


container.export('TGC', house_uuid='3fcc64f4-0000-4000-8000-b517afa9958e')
data = json.loads((tmp / 'tgc' / 'import.json').read_text())

assert data['houseUuid'] == '3fcc64f4-0000-4000-8000-b517afa9958e', data
assert data['teams'] == [
    {'name': 'Red', 'tag': 'RED', 'color': 'Dark Red', 'friendlyFire': False},
], data['teams']

group = data['groups'][0]
assert group['name'] == 'VIP'
assert group['tagShownInChat'] is True
assert group['priority'] == 5
assert group['chatSpeed'] == 'Slow 1s'
assert group['defaultGameMode'] == 'ADVENTURE'
assert group['permissions'] == {
    'Fly': True,
    'Build': True,
    '/tp': True,
    'Ban': False,
}, group['permissions']

command = data['commands'][0]
assert command['name'] == 'warp'
assert command['mode'] == 'Self'
assert command['requiredPriority'] == 3
assert command['listed'] is True
assert command['actions'] == 'commands/warp.htsl'
assert (
    (tmp / 'tgc' / 'commands' / 'warp.htsl')
    .read_text()
    .rstrip()
    .endswith(
        'changePlayerGroup "VIP" true',
    )
)

npc = data['npcs'][0]
assert npc['leftClickRedirect'] is True, npc
assert npc['lookAtPlayers'] is True
assert npc['skin'] == 'Alex'


# houseUuid lands only on the entry import.json, and only when asked for.
with Container() as plain:

    @create_command('noop')
    def _noop() -> None:
        chat('noop')


plain.export('No Uuid')
assert 'houseUuid' not in json.loads((tmp / 'no-uuid' / 'import.json').read_text())


# A permission in both allow and deny is a mistake, not a silent last-wins.
raised = False
with Container():
    try:
        create_group('Bad', allow=['Fly'], deny=['Fly'])
    except ValueError:
        raised = True
assert raised, 'expected a ValueError for a permission in both allow and deny'


# Tags are restricted to letters, digits and spaces; priority to 0-20.
raised = False
with Container():
    try:
        create_team('Bad', tag='no-dashes')
    except ValueError:
        raised = True
assert raised, "expected a ValueError for tag='no-dashes'"

raised = False
with Container():
    try:
        create_group('Bad', priority=21)
    except ValueError:
        raised = True
assert raised, 'expected a ValueError for priority 21'

raised = False
with Container():
    try:

        @create_command('bad', required_priority=99)
        def _bad() -> None:
            chat('x')
    except ValueError:
        raised = True
assert raised, 'expected a ValueError for required_priority 99'
