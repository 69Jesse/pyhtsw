# Items

An `Item` describes a Minecraft item stack. `Item(...)` builds a value;
`.declare()` (or a click handler) registers it as an importable under a name of
its own (see [Importables](./importables.md)).

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

Actions like `give_item` take the item itself; **you never pass a raw string**:

```python
from pyhtsw import give_item, Item


# A declared item -> referenced by its declared htsw name
reward = Item('gold_ingot', name='&6Reward').declare('Reward')
give_item(reward)

# A plain item -> promoted to an items[] entry with a derived name
give_item(Item('apple'))

# Load one from an existing .snbt file
give_item(Item.from_path('items/some-item.snbt'))
```

- `.declare()` names the item up front, so every reference to it uses that
  name, and it returns the item so the call chains off the constructor. Pass a
  name to choose one; without it the name is derived. An item given a click
  handler declares itself too.
- A plain `Item(...)` is given a name and an `items[]` entry of its own at
  export, so htsw lists it in the Project view and can open it in the Item
  Editor. Its `.snbt` is written under the module that built it.
- Use `Item.from_path('....snbt')` to load one from a file rather than passing a
  string.
- Layer variants with `cloned()`, which copies the item overriding only the
  fields you name.

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

## Behaviour

An item's click handler should trigger a function rather than do the work
inline. Housing binds the actions into every copy of the item that has already
been handed out, and those copies cannot be re-bound; the function they trigger
can still be edited. `consumeItem` is the one action that has to stay on the
item. See [Inlining](./inlining.md).

## Matching an item

`HasItem` (and the actions that take an item to find) defaults to
`what_to_check='metadata'`, which compares the **whole** NBT — name, lore,
enchantments, count-independent tags, all of it. So editing an item's lore does
not update the copies already in circulation; it makes them stop matching, and a
check written against the new item quietly sees nothing.

Pass `what_to_check='item_type'` when only the material matters, and treat a
lore edit on an item players already hold as a migration rather than a tweak.

## Copies

`item.cloned(...)` overrides only what you name and keeps the rest, click
handlers included — a stack of three of an ability item is still that ability
item. Pass `on_click=None` to make a copy inert, which is what a menu icon of a
purchasable item wants: clicking the icon buys one, it does not use one.

```python
WAND = Item('blaze_rod', name='&dWand', on_right_click=cast_spell)

WAND.cloned(count=3)  # three wands, still castable
WAND.cloned(lore=price, on_click=None)  # the shop's picture of a wand
```

A copy that comes out byte-identical to an item already declared is not a
second item: it shares the original's name. Otherwise the copy is named after
its stack size, the same way `Item(key, count=n)` always has been.

## The Housing Menu item

Hypixel's own menu item comes in three tiers, and `Item.housing_menu()` builds
whichever one you ask for — the owner's nether star by default, since that is
almost always the one you want. Handing one out is how a player gets the menu
without the permission that normally grants it.

```python
Item.housing_menu()  # OWNER, a nether star
Item.housing_menu('TRUSTED_BUILDER')  # a ghast tear
Item.housing_menu('GUEST')  # a dark oak door
```

`housing_menu_tier='OWNER'` is also a plain `Item` keyword, if you want the
`ExtraAttributes.HOUSING_MENU` tag on something of your own.

## SNBT

```python
print(Item(key='apple').into_snbt())  # indent=4 (default)
print(Item(key='apple').into_snbt(indent=None))  # compact
```

`hide_flags=` sets the `HideFlags` mask directly, overriding the
`hide_*_flag` booleans. It exists for items whose exact bytes are dictated by
someone else — Hypixel writes `255` on the Housing Menu item, a bit beyond the
seven flags `hide_all_flags` knows about — and reading such an item back with
`Item.from_snbt` keeps the mask verbatim so it round-trips.

`Item.into_snbt(indent=4)` produces indented SNBT; pass `indent=None` for a
compact one-line form.

## Interaction keys

htsw assigns and manages item interaction keys automatically on import — you do
**not** manage them in PyHTSW.

See htsw's `language/src/importjson/schemaSpec.ts` for the item section.
