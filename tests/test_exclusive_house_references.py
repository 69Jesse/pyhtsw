import json
import tempfile
from pathlib import Path

from pyhtsw import (
    Container,
    Group,
    HasGroup,
    HasTeam,
    IfAll,
    Menu,
    Region,
    Team,
    TeamStat,
    UndeclaredReferenceError,
    WithinRegion,
    change_player_group,
    chat,
    display_menu,
    function,
    set_player_team,
    trigger_function,
)

tmp = Path(tempfile.mkdtemp())
UUID = '3fcc64f4-0000-4000-8000-b517afa9958e'


def export_exclusive(container: Container, name: str) -> None:
    container.export(name, house_uuid=UUID, exclusive_house=True)


# Every kind htsw's checkUndeclaredReferences flags, each referenced by a plain
# name the container never declares, each reported in one error.
with Container(projects_folder=tmp) as undeclared:

    @function('Dispatch')
    def _dispatch() -> None:
        trigger_function('Elsewhere')
        display_menu('Shop')
        set_player_team('Green')
        change_player_group('VIP')
        with IfAll(WithinRegion('Spawn')):
            chat('in spawn')


try:
    export_exclusive(undeclared, 'Undeclared')
except UndeclaredReferenceError as e:
    message = str(e)
    for line in (
        'Dispatch: function "Elsewhere" (function "Elsewhere" false)',
        'Dispatch: menu "Shop" (displayMenu "Shop")',
        'Dispatch: team "Green" (setTeam "Green")',
        'Dispatch: group "VIP" (changePlayerGroup "VIP" true)',
        'Dispatch: region "Spawn" (inRegion "Spawn")',
    ):
        assert line in message, (line, message)
    assert '@function(...), Menu(...), Region(...), Team(...), Group(...)' in message
else:
    raise AssertionError('undeclared references must fail an exclusive export')
assert not (tmp / 'undeclared').exists()

# The same project exports fine when it does not claim the house.
undeclared.export('Undeclared', house_uuid=UUID)
assert (tmp / 'undeclared' / 'import.json').exists()


# Declared values pass, as does a name that only differs in case or padding
# (Housing resolves names case-insensitively) and the built-in team None.
# hasTeam, hasGroup and team stats are not checked, mirroring htsw.
with Container(projects_folder=tmp) as declared:
    Team('Red', tag='Red', color='red', friendly_fire=True)
    Group('VIP', priority=5)
    Region('Spawn', ((0, 0, 0), (10, 10, 10)))
    Menu('Shop', 3)

    @function('Target')
    def _target() -> None:
        chat('hi')

    @function('Dispatch')
    def _dispatch() -> None:
        trigger_function(' target ')
        display_menu('SHOP')
        set_player_team('red')
        set_player_team('None')
        change_player_group('vip')
        with IfAll(WithinRegion('spawn'), HasTeam('Blue'), HasGroup('Ghost')):
            chat(f'{TeamStat("score", team="Blue")}')


export_exclusive(declared, 'Declared')
data = json.loads((tmp / 'declared' / 'import.json').read_text())
assert data['dangerouslyDeleteEverythingNotInThisFile'] is True
assert [team['name'] for team in data['teams']] == ['Red']
