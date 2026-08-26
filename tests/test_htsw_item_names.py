import json
import sys
import tempfile
import types
from pathlib import Path

from pyhtsw import (
    NPC,
    Container,
    HasItem,
    IfAll,
    Item,
    Menu,
    chat,
    function,
    give_item,
    set_projects_folder,
)

tmp = Path(tempfile.mkdtemp())
set_projects_folder(tmp, save=False)


def load(root: Path, relpath: str = 'import.json') -> dict:
    return json.loads((root / relpath).read_text(encoding='utf-8'))


def items_of(root: Path, relpath: str = 'import.json') -> dict[str, str]:
    return {item['name']: item['nbt'] for item in load(root, relpath).get('items', [])}


with Container() as naming:

    @function('Names')
    def names() -> None:
        give_item(Item('gold_ingot', name='&6Coin'))  # display name
        give_item(Item('apple'))  # vanilla title
        give_item(Item('apple', count=3))  # ...plus the stack size
        # Same display name, different stack sizes -> the size separates them,
        # and it is applied to every member so no row is left ambiguous.
        give_item(Item('paper', name='&bTicket', count=2))
        give_item(Item('paper', name='&bTicket', count=5))
        # Nothing but NBT separates these two -> numbers, the honest last resort.
        give_item(Item('bow', damage=1))
        give_item(Item('bow', damage=2))


naming.export('Naming')
naming_root = tmp / 'naming'
naming_items = items_of(naming_root)
assert set(naming_items) == {
    'Coin',
    'Apple',
    'Apple x3',
    'Ticket x2',
    'Ticket x5',
    'Bow',
    'Bow 2',
}, naming_items
# Files are named after the item, not a content hash.
assert naming_items['Apple x3'] == 'items/apple-x3.snbt'
assert naming_items['Ticket x5'] == 'items/ticket-x5.snbt'

text = (naming_root / 'functions' / 'names.htsl').read_text(encoding='utf-8')
assert '.snbt' not in text
assert 'giveItem "Ticket x2"' in text


with Container() as shared_c:
    coin = Item('gold_ingot', name='&6Coin')
    twin = Item('gold_ingot', name='&6Coin')  # equal NBT -> same file and name
    badge = Item('emerald', name='&aBadge')  # menu-only, never in an action

    purse = Menu('Purse', 1)

    @purse.add_element(coin, x=0, y=0)
    def _take() -> None:
        chat('took')

    @purse.add_element(badge, x=0, y=1)
    def _look() -> None:
        chat('looked')

    NPC('Teller', (0, 0, 0), equipment=NPC.Equipment(hand=twin))

    @function('Pay')
    def pay() -> None:
        give_item(twin)
        with IfAll(HasItem(coin)):
            chat('paid')


shared_c.export('Shared')
shared_root = tmp / 'shared'
shared_items = items_of(shared_root)
# The coin is referenced from an action, so it is promoted exactly once even
# though four different places use it.
assert set(shared_items) == {'Coin'}, shared_items
assert shared_items['Coin'] == 'items/coin.snbt'
assert len(list((shared_root / 'items').glob('*.snbt'))) == 2  # coin + badge

data = load(shared_root)
# Menu slots and NPC equipment take a path, not a name (htsw's schema types
# those fields as snbtPath), and they point at the very same file.
assert data['npcs'][0]['equipment'] == {'hand': 'items/coin.snbt'}
slots = {slot['slot']: slot['nbt'] for slot in data['menus'][0]['slots']}
assert slots[0] == 'items/coin.snbt'
# A menu-only item is not promoted, but still gets a readable filename.
assert slots[1] == 'items/badge.snbt'

# Both the action and the condition reference it by name.
pay_text = (shared_root / 'functions' / 'pay.htsl').read_text(encoding='utf-8')
assert 'giveItem "Coin"' in pay_text
assert 'hasItem "Coin"' in pay_text


with Container() as opted:

    @function('Opted')
    def opted_fn() -> None:
        give_item(Item('bone', name='&fSecret', importable=False))


opted.export('Opted')
opted_root = tmp / 'opted'
assert 'items' not in load(opted_root)
opted_text = (opted_root / 'functions' / 'opted.htsl').read_text(encoding='utf-8')
assert 'giveItem "../items/secret.snbt"' in opted_text


factory = types.ModuleType('fakepkg.factory')
exec(  # noqa: S102
    'from pyhtsw import Item\n\ndef make(key, name):\n    return Item(key, name=name)\n',
    factory.__dict__,
)
sys.modules['fakepkg.factory'] = factory

consumer = types.ModuleType('fakepkg.consumer')
consumer.__dict__['make'] = factory.make
exec("WIDGET = make('stick', '&aWidget')", consumer.__dict__)  # noqa: S102
assert consumer.WIDGET.__htsw_module__ == 'fakepkg.consumer'

# The same item built in two modules folds into one file, owned by the first
# module in sorted order so the choice never depends on evaluation order.
elsewhere = types.ModuleType('fakepkg.alpha')
elsewhere.__dict__['make'] = factory.make
exec("WIDGET = make('stick', '&aWidget')", elsewhere.__dict__)  # noqa: S102

with Container() as attributed:

    @function('Use Widget')
    def use_widget() -> None:
        give_item(consumer.WIDGET)
        give_item(elsewhere.WIDGET)


use_widget.__htsw_importable__.module = 'fakepkg.consumer'
attributed.export('Attributed')
attributed_root = tmp / 'attributed'

assert items_of(attributed_root, 'alpha/import.json') == {'Widget': 'items/widget.snbt'}
assert 'items' not in load(attributed_root, 'consumer/import.json')
assert (attributed_root / 'alpha' / 'items' / 'widget.snbt').exists()
# The consumer node reaches the item it names through a cross-module include.
assert load(attributed_root, 'consumer/import.json')['include'] == [
    '../alpha/import.json',
]

widget_text = (
    attributed_root / 'consumer' / 'functions' / 'use-widget.htsl'
).read_text(encoding='utf-8')
assert widget_text.count('giveItem "Widget"') == 2

print('test_htsw_item_names passed')
