import tempfile
from pathlib import Path

from pyhtsw.importable import Project
from pyhtsw.limits import packing_cost
from pyhtsw.schedule import reorder_for_packing

from pyhtsw import (
    ActionLimitError,
    Container,
    Enchantment,
    IfAll,
    Item,
    PlayerStat,
    chat,
    create_event,
    create_function,
    create_menu,
)

y = PlayerStat('y').as_long()


def _icons(container: Container) -> dict[str, dict | None]:
    project = Project(Path(tempfile.mkdtemp()))
    icons: dict[str, dict | None] = {}
    for importable in container.importables:
        icon = getattr(importable, 'icon', None)
        icons[importable.identifier()] = project.icon(icon) if icon else None
    return icons


def _spill(count: int = 1400) -> None:
    for i in range(count):
        chat(f'x{i}')


# === A function still spills, and the icon's stack follows the name ===

with Container() as container:

    @create_function(
        'Big',
        icon=Item('diamond_sword', enchantments=[Enchantment('sharpness', 3)]),
    )
    def _big() -> None:
        _spill()


icons = _icons(container)
assert 'Big 2' in icons and 'Big 3' in icons, icons
assert icons['Big'] == {'item': 'minecraft:diamond_sword', 'enchanted': True}, icons
assert icons['Big 2'] == {
    'item': 'minecraft:diamond_sword',
    'count': 2,
    'enchanted': True,
}, icons
assert icons['Big 3'] == {
    'item': 'minecraft:diamond_sword',
    'count': 3,
    'enchanted': True,
}, icons


# === The count starts from the source's own and clamps at 64 ===

with Container() as container:

    @create_function('Stacked', icon=Item('paper', count=62))
    def _stacked() -> None:
        _spill(2200)


icons = _icons(container)
assert icons['Stacked 2'] == {'item': 'minecraft:paper', 'count': 63}, icons
assert icons['Stacked 3'] == {'item': 'minecraft:paper', 'count': 64}, icons
assert icons['Stacked 4'] == {'item': 'minecraft:paper', 'count': 64}, icons


# === No icon on the source, none on the spill ===

with Container() as container:

    @create_function('Plain')
    def _plain() -> None:
        _spill()


icons = _icons(container)
assert 'Plain 2' in icons, icons
assert icons['Plain 2'] is None, icons


# === A name the consumer already owns is skipped, and the count follows ===

with Container() as container:

    @create_function('Big 2', icon=Item('apple'))
    def _decoy_two() -> None:
        chat('decoy')

    @create_function('Big 3')
    def _decoy_three() -> None:
        chat('decoy')

    @create_function('Big', icon=Item('diamond_sword'))
    def _big_again() -> None:
        _spill()


icons = _icons(container)
assert 'Big 4' in icons, icons
assert icons['Big 2'] == {'item': 'minecraft:apple'}, icons
assert icons['Big 4'] == {'item': 'minecraft:diamond_sword', 'count': 4}, icons


# === A menu slot raises instead, naming every offender by its handler ===

try:
    with Container() as container:
        panel = create_menu('Panel', 3)

        @panel.on(item=Item('stone'), x=0, y=0)
        def buy_sword() -> None:
            _spill(700)

        @panel.on(item=Item('dirt'), x=0, y=1)
        def sell_all() -> None:
            _spill(700)

except ActionLimitError as error:
    message = str(error)
else:
    raise AssertionError('expected an over-limit menu slot to raise')

assert isinstance(ActionLimitError('x'), RuntimeError)
# Both offenders in one error, not one run per block.
assert 'Panel slot buy_sword' in message, message
assert 'Panel slot sell_all' in message, message
assert 'menu "Panel slot buy_sword"' in message, message
assert '@create_function' in message, message
assert '4 ticks' in message, message
# Nothing was carved out on the way to the error.
assert not any(
    importable.kind == 'functions' for importable in container.importables
), [importable.identifier() for importable in container.importables]


# The blocks were rewritten in place on the way to the error, so a second
# finalize has to fail the same way instead of fixing them twice.
try:
    container.finalize()
except ActionLimitError as error:
    assert str(error) == message, (str(error), message)
else:
    raise AssertionError('expected a re-finalize to raise again')


# === Same for an event, which is over its (larger) budget ===

try:
    with Container() as container:

        @create_event('Player Join')
        def _on_join() -> None:
            _spill(1400)

except ActionLimitError as error:
    message = str(error)
else:
    raise AssertionError('expected an over-limit event to raise')

assert 'event "event Player Join"' in message, message


# === ignore_action_limits is still the way past it ===

with Container(ignore_action_limits=True) as container:
    quiet = create_menu('Quiet', 3)

    @quiet.on(item=Item('stone'), x=0, y=0)
    def open_it() -> None:
        _spill(700)


assert not any(
    importable.kind == 'functions' for importable in container.importables
), [importable.identifier() for importable in container.importables]


# === Fitting is worth spending wrappers on, so the packer optimises for it ===


def _interleaved(conditionals: int, chats: int) -> list:
    with Container(ignore_action_limits=True) as raw:

        @create_function('probe')
        def _probe() -> None:
            for i in range(conditionals):
                with IfAll(PlayerStat('x') > i):
                    y.value += 1
                for j in range(chats):
                    chat(f'm{i}-{j}')

    return next(
        block for block in raw.blocks if block.get_name() == 'probe'
    ).expressions


expressions = _interleaved(20, 3)
source_cost = packing_cost(expressions, importable='menus', allow_functions=False)
assert source_cost[0] > 0, source_cost

reordered = reorder_for_packing(
    expressions,
    importable='menus',
    allow_functions=False,
)
assert reordered is not None
reordered_cost = packing_cost(reordered, importable='menus', allow_functions=False)
# Leftover is the term that decides between a build and an error; wrappers are
# free by comparison, so it is allowed to spend more of them.
assert reordered_cost[0] == 0, (source_cost, reordered_cost)

# And it really does rescue the block end to end.
with Container() as container:
    shop = create_menu('Shop', 3)

    @shop.on(item=Item('stone'), x=0, y=0)
    def open_shop() -> None:
        for i in range(20):
            with IfAll(PlayerStat('x') > i):
                y.value += 1
            for j in range(3):
                chat(f'm{i}-{j}')


assert not any(
    importable.kind == 'functions' for importable in container.importables
), [importable.identifier() for importable in container.importables]

# With a function available the objective is unchanged: cost the spill, not the
# leftover.
with_functions = packing_cost(expressions, importable='menus')
assert with_functions[0] > 0, with_functions
