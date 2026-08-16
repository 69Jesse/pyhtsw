# Items

An `Item` describes a Minecraft item stack. Construct one directly or declare a
subclass (which also registers it as an importable — see
[Importables](./importables.md)).

```python
from pyhtsw import Item, Enchantment


sword = Item(
    key='diamond_sword',
    name='&bFrostbrand',
    lore='&7A chilling blade.\n&7Drops snow.',
    count=1,
    enchantments=[Enchantment('sharpness', 5)],
)
```

Common keyword arguments: `key` (required), `name`, `lore` (use `\n` for line
breaks), `count`, `enchantments`, `unbreakable`, `damage`, `color`,
`skull_data`, and the `hide_*_flag` toggles.

## Referencing items from actions

Actions like `give_item` accept an item as a class or an instance; **you never
pass a raw string**:

```python
from pyhtsw import give_item, Item


# A declared subclass (the class) -> referenced by its htsw name
class Reward(Item, key='gold_ingot', name='&6Reward'):
    pass


give_item(Reward)

# A plain instance -> promoted to an items[] entry with a derived name
give_item(Item(key='apple'))

# Load an instance from an existing .snbt file
give_item(Item.from_path('items/some-item.snbt'))
```

- Pass an `Item` **subclass** to reference a declared item by its class name.
- Pass an `Item` **instance** and export gives it a name and an `items[]` entry
  of its own, so htsw lists it in the Project view and can open it in the Item
  Editor. Its `.snbt` is written under the module that built it.
- Use `Item.from_path('....snbt')` to load an instance from a file rather than
  passing a string.

### Generated names

The name comes from the item's display name with formatting stripped, or from
its vanilla title plus the stack size when it has no display name. Two items
that render the same SNBT are one file, one name and one entry, however many
modules build them.

| Item | Name |
| --- | --- |
| `Item('gold_ingot', name='&6Coin')` | `Coin` |
| `Item('apple')` | `Apple` |
| `Item('oak_log', count=16)` | `Oak Log x16` |

When several different items want the same name, the tiebreaker is whatever
actually tells them apart — the stack size, then the owning module, then a
number as a last resort — and it is applied to every item in the clash, so no
entry is left ambiguous:

```python
give_item(Item('paper', name='&bTicket', count=2))  # -> "Ticket x2"
give_item(Item('paper', name='&bTicket', count=5))  # -> "Ticket x5"
```

Pass `importable=False` to keep an item out of `import.json`; it stays a direct
`.snbt` path reference (but still gets a readable filename).

Menu slots and NPC equipment are unaffected: htsw's schema types those fields as
`.snbt` paths, so they always reference the file. They are already clickable in
the Project view, and they share the file with any action that uses the same
item.

## SNBT

```python
print(Item(key='apple').into_snbt())          # indent=4 (default)
print(Item(key='apple').into_snbt(indent=None))  # compact
```

`Item.into_snbt(indent=4)` produces indented SNBT; pass `indent=None` for a
compact one-line form.

## Interaction keys

htsw assigns and manages item interaction keys automatically on import — you do
**not** manage them in PyHTSW.

See htsw's `language/src/importjson/schemaSpec.ts` for the item section.
