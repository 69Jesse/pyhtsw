import json
import tempfile
from pathlib import Path

from pyhtsw import (
    NPC,
    Container,
    Group,
    Team,
    change_player_group,
    chat,
    command,
    set_player_team,
    set_projects_folder,
)

tmp = Path(tempfile.mkdtemp())
set_projects_folder(tmp, save=False)


# A declared team is the same Team value the actions already take.
with Container() as container:
    red = Team('Red', tag='RED', color='dark_red', friendly_fire=False)
    vip = Group(
        'VIP',
        tag='VIP',
        tag_shown_in_chat=True,
        color='gold',
        priority=5,
        allow=['fly', 'build', 'tp'],
        deny=['ban'],
        chat_speed='slow_1s',
        default_gamemode='adventure',
    )

    @command('warp', mode='self', required_priority=3, listed=True)
    def _warp() -> None:
        set_player_team(red)
        change_player_group(vip)

    greeter = NPC(
        '&aGreeter',
        (1, 2, 3),
        left_click_redirect=True,
        look_at_players=True,
        skin='alex',
    )

    @greeter.on_right_click
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

command_entry = data['commands'][0]
assert command_entry['name'] == 'warp'
assert command_entry['mode'] == 'Self'
assert command_entry['requiredPriority'] == 3
assert command_entry['listed'] is True
assert command_entry['actions'] == 'commands/warp.htsl'
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

    @command('noop')
    def _noop() -> None:
        chat('noop')


plain.export('No Uuid')
assert 'houseUuid' not in json.loads((tmp / 'no-uuid' / 'import.json').read_text())


# A permission in both allow and deny is a mistake, not a silent last-wins.
raised = False
with Container():
    try:
        Group('Bad', allow=['fly'], deny=['fly'])
    except ValueError:
        raised = True
assert raised, 'expected a ValueError for a permission in both allow and deny'


# Tags are restricted to letters, digits and spaces; priority to 0-20.
raised = False
with Container():
    try:
        Team('Bad', tag='no-dashes')
    except ValueError:
        raised = True
assert raised, "expected a ValueError for tag='no-dashes'"

raised = False
with Container():
    try:
        Group('Bad', priority=21)
    except ValueError:
        raised = True
assert raised, 'expected a ValueError for priority 21'

raised = False
with Container():
    try:

        @command('bad', required_priority=99)
        def _bad() -> None:
            chat('x')
    except ValueError:
        raised = True
assert raised, 'expected a ValueError for required_priority 99'
