import json
import tempfile
from pathlib import Path

from pyhtsw import (
    Container,
    Item,
    Location,
    chat,
    function,
    give_item,
    normalize_item,
    set_projects_folder,
)
from pyhtsw.location import resolve_location

tmp = Path(tempfile.mkdtemp())
set_projects_folder(tmp, save=False)


# Duplicate importable names raise.
with Container():

    @function('dup')
    def _a() -> None:
        chat('a')

    raised = False
    try:

        @function('dup')
        def _b() -> None:
            chat('b')
    except RuntimeError:
        raised = True
    assert raised, 'expected a RuntimeError for the duplicate function name'


# Top-level actions get wrapped into a function named after the project.
with Container() as wrap:
    chat('written outside any importable')
wrap.export('Wrap Test')
data = json.loads((tmp / 'wrap-test' / 'import.json').read_text())
assert any(fn['name'] == 'Wrap Test' for fn in data['functions'])


# Items never accept plain strings.
for bad in ('a string', 123, None):
    raised = False
    try:
        normalize_item(bad)  # type: ignore[arg-type]
    except TypeError:
        raised = True
    assert raised, f'normalize_item should reject {bad!r}'


# A bare Location is not a valid location; the concrete ones are.
raised = False
try:
    resolve_location(Location())
except TypeError:
    raised = True
assert raised, 'bare Location() should be rejected'

assert resolve_location(Location.house_spawn()) == ('house_spawn', None)
assert resolve_location(Location.custom(1, 2, 3)) == ('custom_coordinates', '1 2 3')


# A declared item references by its declared name; a plain one is promoted to
# an items[] entry and referenced by a derived name, never by path.
with Container() as c:
    sword = Item('diamond_sword', name='&bSword')

    give_item(sword)  # by declared name
    give_item(Item('apple'))  # no display name -> the vanilla title
    give_item(Item('apple', count=3))  # ...plus the stack size
    give_item(Item('gold_ingot', name='&6Coin'))  # display name wins
    give_item(Item('bone', name='&fSecret', importable=False))  # opted out
c.export('Ref Test')
ref_root = tmp / 'ref-test'
text = (ref_root / 'functions' / 'ref-test.htsl').read_text()
assert 'giveItem "Sword"' in text
assert 'giveItem "Apple"' in text
assert 'giveItem "Apple x3"' in text
assert 'giveItem "Coin"' in text
# `importable=False` stays a path reference, relative to the action file, but
# still gets a readable filename rather than a content hash.
assert 'giveItem "../items/secret.snbt"' in text

ref_items = json.loads((ref_root / 'import.json').read_text())['items']
assert {item['name'] for item in ref_items} == {'Sword', 'Apple', 'Apple x3', 'Coin'}
assert {item['nbt'] for item in ref_items} == {
    'items/sword.snbt',
    'items/apple.snbt',
    'items/apple-x3.snbt',
    'items/coin.snbt',
}
