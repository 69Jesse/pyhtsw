import json
import tempfile
from pathlib import Path
from types import ModuleType

import pyhtsw
from pyhtsw import (
    Container,
    Item,
    chat,
    create_function,
    give_item,
    set_projects_folder,
    trigger_function,
)

tmp = Path(tempfile.mkdtemp())
set_projects_folder(tmp, save=False)

with Container() as container:

    @create_function('Ability')
    def ability() -> None:
        chat('cast')

    @create_function('Combat')
    def combat() -> None:
        chat('hit')

    # An anonymous item owned by items.abilities but handed out from a function
    # in features.cookie -> its .snbt must live under the abilities folder.
    potion = Item('potato', name='&aPotion')

    @create_function('Cookie')
    def cookie() -> None:
        chat('tick')
        # cross-module edge: features.cookie -> items.abilities
        trigger_function(ability)
        give_item(potion)

    # Mutually-recursive functions in two modules -> an include cycle that must
    # be broken (exactly one direction kept).
    @create_function('PingA')
    def ping_a() -> None:
        trigger_function('PingB')

    @create_function('PingB')
    def ping_b() -> None:
        trigger_function('PingA')


potion.__htsw_module__ = 'items.abilities'
ability.__htsw_importable__.module = 'items.abilities'
combat.__htsw_importable__.module = 'features.general.combat'
cookie.__htsw_importable__.module = 'features.cookie'
ping_a.__htsw_importable__.module = 'modx'
ping_b.__htsw_importable__.module = 'mody'

container.export('Tree Demo')
root = tmp / 'tree-demo'


def load(relpath: str) -> dict:
    return json.loads((root / relpath).read_text(encoding='utf-8'))


def includes(relpath: str) -> set[str]:
    return set(load(relpath).get('include', []))


# Root mirrors the top-level packages/modules (kebab-case), not the functions.
# No `modules/` wrapper; a module named `items` is suffixed to dodge the
# collision with a node's own `items/` folder.
assert 'functions' not in load('import.json')
assert includes('import.json') == {
    'features/import.json',
    'items-module/import.json',
    'modx/import.json',
    'mody/import.json',
}

# Packages include their children; the leaf holds the actual function.
assert includes('features/import.json') == {
    'cookie/import.json',
    'general/import.json',
}
assert includes('features/general/import.json') == {
    'combat/import.json',
}
combat_node = load('features/general/combat/import.json')
assert {fn['name'] for fn in combat_node['functions']} == {'Combat'}

# Cross-module reference -> include edge into the other subtree, with a relative
# path that resolves to the abilities import.json.
cookie_dir = root / 'features/cookie'
cookie_includes = includes('features/cookie/import.json')
assert len(cookie_includes) == 1
(edge,) = cookie_includes
assert (cookie_dir / edge).resolve() == (
    root / 'items-module/abilities/import.json'
).resolve()

# The cycle is broken: exactly one of the two directions survives.
modx_to_mody = 'mody' in str(includes('modx/import.json'))
mody_to_modx = 'modx' in str(includes('mody/import.json'))
assert modx_to_mody != mody_to_modx, (modx_to_mody, mody_to_modx)

# The potion is promoted to an items[] entry in its owning module's node
# (items.abilities), named after its display name, with the .snbt beside it.
abilities_node = load('items-module/abilities/import.json')
assert [item['name'] for item in abilities_node['items']] == ['Potion']
assert abilities_node['items'][0]['nbt'] == 'items/potion.snbt'
assert (root / 'items-module/abilities/items/potion.snbt').exists()

# The give-item action in features.cookie refers to it by name, not by path,
# which is what the cross-module include edge above exists to resolve.
give = (cookie_dir / 'functions/cookie.htsl').read_text(encoding='utf-8')
assert 'giveItem "Potion"' in give
assert '.snbt' not in give

# Exporting a single module roots it at the project root, with anything it pulls
# in from another package nesting as a referenced sub-project.
with Container():

    @create_function('Leaf')
    def leaf() -> None:
        trigger_function('Dep')

    @create_function('Dep')
    def dep() -> None:
        chat('dep')


leaf.__htsw_importable__.module = 'pkg.leaf'
dep.__htsw_importable__.module = 'other.dep'

module = ModuleType('pkg.leaf')
module.leaf = leaf  # type: ignore[attr-defined]
module.dep = dep  # type: ignore[attr-defined]
pyhtsw.export(module, 'Mod Root')

mod_root = tmp / 'mod-root'
mod_data = json.loads((mod_root / 'import.json').read_text(encoding='utf-8'))
# the exported module's own function is at the root...
assert {fn['name'] for fn in mod_data['functions']} == {'Leaf'}
# ...and its out-of-package dependency nests under its real path.
assert 'other/import.json' in mod_data.get('include', [])
dep_data = json.loads(
    (mod_root / 'other/dep/import.json').read_text(encoding='utf-8'),
)
assert {fn['name'] for fn in dep_data['functions']} == {'Dep'}

print('test_htsw_module_tree passed')
