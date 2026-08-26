# Importables

Importables are the entities HTSW imports: functions, events, items, regions,
menus, NPCs, teams, groups and commands. See htsw's
`language/src/importjson/schemaSpec.ts` for the underlying import.json schema.

**Every kind is declared the same way: a `create_*` factory.** The ones that own
a single action list (`create_function`, `create_command`, `create_event`) are
decorators; the rest are plain calls. Each returns a **value** — a `Function`,
`Menu`, `Region`, `Item`, ... — that you pass to actions, and that answers for
its own declaration:

```python
shop = create_menu('Magic Shop', 6)

shop.name   # 'Magic Shop'
shop.size   # 6
```

Every field of a declaration reads back off the value, and every field except
`name` can be set on it afterwards. `value.importable` is the declaration
itself, for the rare case you want the raw `import.json` entry.

## Functions

```python
from pyhtsw import create_function, chat


@create_function('Tick', repeat_ticks=20, icon=Clock)
def tick() -> None:
    chat('one second passed')
```

- `repeat_ticks` runs the function on an interval (optional). It is part of
  the function's definition, so the project is the source of truth for it:
  re-importing a looping function without `repeat_ticks` stops the loop in
  the house.
- `icon` is an `Item` (optional).

A house may hold **200 functions** in total, so a function is worth declaring
only when the actions have to be one shared thing. A menu slot or command whose
whole body triggers a single-use function should hold the actions itself
instead; an item's behaviour should always be a function. See
[Inlining](./inlining.md).

## Events

```python
from pyhtsw import create_event, chat


@create_event('Player Join')
def on_join() -> None:
    chat('&aSomeone joined!')
```

`create_event` returns an `Event` value, the way `create_function` returns a
`Function`. Housing fires it, so — like a `Command` — it cannot be triggered
from HTSL; the value is there to name the event and to be re-exported.

The event name is typed to the 18 htsw events (`Player Join`, `Player Quit`,
`Player Death`, `Player Kill`, `Player Respawn`, `Group Change`,
`PvP State Change`, `Fish Caught`, `Player Enter Portal`, `Player Damage`,
`Player Block Break`, `Start Parkour`, `Complete Parkour`, `Player Drop Item`,
`Player Pick Up Item`, `Player Change Held Item`, `Player Toggle Sneak`,
`Player Toggle Flight`).

## Items, Regions, NPCs, Menus

These four own action lists — clicks, region enter/exit — so they are declared
by a call and their handlers are attached to the value it returns. Handlers are
callables that take **0 args, or 1 arg** that receives the value they belong to.

Each takes its handlers as keyword arguments, or as decorators afterwards:

| Importable | Decorators | Keyword shorthands |
|---|---|---|
| `Item` | `@item.left_click`, `@item.right_click`, `@item.click` | `on_left_click=`, `on_right_click=`, `on_click=` |
| `Region` | `@region.on_enter`, `@region.on_exit` | `on_enter=`, `on_exit=` |
| `NPC` | `@npc.left_click`, `@npc.right_click`, `@npc.click` | `on_left_click=`, `on_right_click=`, `on_click=` |
| `Menu` | `@menu.on(item=, slot=)` | — |

```python
from pyhtsw import chat, create_item


# Decorator form
wand = create_item('blaze_rod', name='&dWand')


@wand.left_click
def cast() -> None:
    chat('zap')


@wand.right_click
def block() -> None:
    chat('block')
```

```python
# Keyword shorthand
def cast() -> None:
    chat('zap')


wand = create_item('blaze_rod', name='&dWand', on_left_click=cast)
```

Because these are ordinary calls, any of them can be built in a loop, and a
handler closes over the loop variable through an ordinary function scope
instead of a default-argument dance.

### Item

`Item(...)` builds a value; `create_item(...)` builds one **and** declares it as
an `items[]` entry, so actions reference it by name and htsw lists it in the
Project view. An item given a click handler declares itself either way. See
[Items](./items.md) for the full field list and how names are derived.

```python
from pyhtsw import chat, create_item, give_item

wand = create_item('blaze_rod', name='&dWand', importable_name='Wand')


@wand.click
def cast() -> None:
    chat('zap')


give_item(wand)
```

- `importable_name=` overrides the derived htsw name; without it the name comes
  from the display name with formatting stripped (`&dWand` -> `Wand`).
- Two items that render the same SNBT are one item to htsw, so the second one
  shares the first's entry rather than registering a duplicate.

### Region

```python
from pyhtsw import chat, create_region


spawn = create_region('Spawn Zone', ((0, 60, 0), (16, 80, 16)))


@spawn.on_enter
def entered() -> None:
    chat('&aentered spawn')


@spawn.on_exit
def left() -> None:
    chat('&7left spawn')
```

- `bounds` is `((x, y, z), (x, y, z))` — the from/to corners — and is
  **optional**: htsw imports a region without them and you place it in-game.
- `region.corners(a, b)` sets `bounds` from two opposite corners in either
  order, the way the in-game region tool hands them to you.
- `region.bounds` is readable and settable after declaration, so a region can be
  declared up front and placed once the coordinates are known.
- `region.attach('enter' | 'exit', handler)` is the non-decorator form, which is
  what a loop wants.

```python
pads = [create_region(f'Pad {n}') for n in range(3)]
for n, pad in enumerate(pads):
    pad.corners((n, 60, 0), (n + 1, 61, 1))
```

`WithinRegion` takes the value, or a bare string for a region declared in-game:

```python
with IfAll(WithinRegion(spawn)):
    chat('&ain spawn')

with IfAll(WithinRegion('Hand Placed')):
    chat('&ein a region pyhtsw never declared')
```

### NPC

```python
from pyhtsw import NPC, Item, chat, create_npc


helmet = Item('diamond_helmet')

guide = create_npc(
    '&bVillage Guide',
    (10, 65, 10),
    skin='Steve',
    look_at_players=True,
    hide_name_tag=False,
    equipment=NPC.Equipment(helmet=helmet),
)


@guide.right_click
def talk() -> None:
    chat('Welcome, traveler.')
```

- `name` is the NPC's displayed name (formatting codes allowed).
- `pos` is `(x, y, z)`.
- `skin` is one of `'Steve'`, `'Alex'`, `'Players Skin'`.
- `left_click_redirect=True` makes a left click run the right-click actions.
- `NPC.Equipment(helmet=, chestplate=, leggings=, boots=, hand=)` — each an
  `Item`.
- A handler taking one argument receives the NPC it belongs to, so it can read
  its own name and position instead of closing over them.
- `npc.attach('left' | 'right' | 'both', handler)` is the non-decorator form.

NPCs generated from data are the common case:

```python
for enemy in ENEMIES:
    def strike(enemy=enemy) -> None:
        chat(f'You strike the {enemy.name}!')

    create_npc(enemy.name, enemy.pos, skin='Steve', on_click=strike)
```

#### on_click

Housing has no "either button" action list. A left click can only be pointed at
the right-click one, which is what `leftClickRedirect` does, so wanting an NPC
that just *responds to being clicked* costs two settings that have to agree.

`on_click` is that pair under one name: it fills the right-click list and turns
the redirect on.

```python
create_npc('&aShopkeeper', (8, 65, 8), on_click=lambda: display_menu(SHOP))
```

It is mutually exclusive with `on_left_click`, `on_right_click` and
`left_click_redirect` — the overloads make passing both a type error, and it is
rejected at runtime too, in whichever order they are applied. Reach for the pair
when the two buttons genuinely do different things, and `on_click` when they
don't.

### Menu

```python
from pyhtsw import Item, chat, close_menu, create_item, create_menu


filler = Item('gray_stained_glass_pane', name=' ')
confirm = create_item('lime_dye', name='&aConfirm')

shop = create_menu('Magic Shop', 6)
shop.fill(filler, xy_check=lambda x, y: (x + y) % 2 == 0)


@shop.on(item=confirm, x=5, y=4)
def buy() -> None:
    close_menu()
```

- `name` is the menu's displayed title. Formatting codes are **not** supported
  here; they render literally (`&aShop` shows as the text `&aShop`).
- `size` is typed `Literal[1, 2, 3, 4, 5, 6]` (rows). Menus are 9 columns wide.
- `menu.on(item=, slot=, x=, y=, xy_check=)` adds a clickable slot;
  `menu.add_element(...)` is the same method under its original name.
  - `slot` is the **flat** index Housing itself uses, `0`–`53`, shorthand for
    `x=slot // 9, y=slot % 9`. It also takes a sequence of indices. Pass either
    `slot=` or `x=`/`y=`, never both.
  - `x` is the **row**, `y` is the **column**. Each is `int | Sequence[int] |
    None`; `None` means every index on that axis.
  - Negative indices are allowed and resolved against the size at render time.
  - `xy_check=lambda x, y: ...` filters cells (e.g. a checkerboard pattern).
- `menu.place(item, slot=/x=/y=/xy_check=)` puts an item down with **no actions
  behind it** — decoration, or a label. It saves writing a handler whose whole
  body is `pass`.
- `menu.fill(item, xy_check=)` places `item` in every cell the check accepts
  (every cell when it is omitted). Later placements win, so fill first.
- `menu.distance_from_edge(x, y)` is how many cells in from the nearest border a
  cell is — `0` on the outer ring, `1` on the next — which is what makes a
  two-tone glass border one line each.
- Later elements override earlier ones per cell. Overriding a cell that a
  fully-explicit element (both `x` and `y` given) already set logs a warning.

A menu built from data — one page per shop category, one per reward tier — is
just the same call in a loop:

```python
from pyhtsw import Menu, create_menu, give_item


def build_page(category) -> Menu:
    menu = create_menu(f'Shop > {category.name}', 6)
    menu.fill(BLACK, xy_check=lambda x, y: menu.distance_from_edge(x, y) == 0)
    menu.fill(GRAY, xy_check=lambda x, y: menu.distance_from_edge(x, y) == 1)
    menu.place(INFO_ITEM, slot=4)

    for slot, entry in zip(SLOTS, category.items, strict=True):

        @menu.on(item=entry.item, slot=slot)
        def _buy(entry=entry) -> None:
            give_item(entry.item)

    return menu


PAGES = [build_page(category) for category in CATEGORIES]
```

Note the loop still binds `entry` through a default argument, because the `for`
body is not its own scope; lifting the loop into a helper that returns the
handler, or building one menu per function call, removes even that.

## Teams and Groups

Teams and groups hold no actions, so `create_team` / `create_group` are the
whole surface. Each returns the same `Team` / `Group` value the actions already
take, so a declared team is used exactly like an undeclared one.

```python
from pyhtsw import create_team, create_group, set_player_team, change_player_group


Red = create_team('Red', tag='RED', color='Dark Red', friendly_fire=False)

VIP = create_group(
    'VIP',
    tag='VIP',
    tag_shown_in_chat=True,
    color='Gold',
    priority=5,
    allow=['Fly', 'Build', 'Use Chests', '/tp'],
    deny=['Ban', 'Kick'],
    chat_speed='Slow 1s',
    default_gamemode='ADVENTURE',
)

set_player_team(Red)
change_player_group(VIP)
Red.stat('kills').value += 1
```

- `tag` may contain only letters, digits and spaces.
- `color` is one of Housing's 14 named colours (`'Dark Blue'` … `'Yellow'`).
- `priority` is `0`–`20`.
- `allow=` / `deny=` are sequences of Housing's 51 permission names, typed as a
  `Literal` so a typo is a type error. A permission left out of both is
  **absent** from `import.json`, which is not the same as denying it. Naming one
  in both raises.
- `permissions={'Fly': True, 'Ban': False}` is the raw 1:1 form, accepted
  alongside `allow`/`deny` as an escape hatch.

As with every kind, each declared field reads back off the value itself —
`VIP.priority`, `VIP.color`, `Red.friendly_fire`. Teams and groups add one thing
the others do not need: a bare `Team(name)` / `Group(name)` is a **reference**,
not a declaration, because Housing ships teams and groups that exist without
one. A reference compares equal to the declared value and resolves the same
fields. A field left out of the declaration reads as `None`; `permissions` comes
back as a read-only view. Reading a name that was never declared in the current
container raises, rather than answering `None` for a group that does not exist
here:

```python
Group('VIP').priority        # 5
create_group('Plain').tag    # None
Group('Ghost').priority      # RuntimeError: ... was never declared ...
```

## Commands

A command owns a single action list, so it is a decorator like
`@create_function`.

```python
from pyhtsw import create_command, chat, teleport_player, Location


@create_command('warp', mode='Self', required_priority=0, listed=True)
def warp() -> None:
    teleport_player(Location.custom(0, 100, 0))
    chat('&aWarped!')
```

- `mode` is `'Self'` or `'Targeted'`.
- `required_priority` is `0`–`20`.
- `listed` controls whether the command shows in the in-game list.

Housing has no trigger-command action, so unlike a `Function` the returned
`Command` cannot be called from other actions.

A command owning its own list is also why a command that only triggers one
single-use function should hold that function's actions directly — see
[Inlining](./inlining.md).

## Binding a house

`import.json` can carry a `houseUuid` that binds the project to one specific
house. It is opt-in and written only into the entry `import.json` — htsw
ignores the field in included files.

```python
import pyhtsw

pyhtsw.set_house_uuid('3fcc64f4-0000-4000-8000-b517afa9958e')

# or, per export, which wins over the global setting:
container.export('MyHouse', house_uuid='3fcc64f4-0000-4000-8000-b517afa9958e')
```
