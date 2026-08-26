# Importables

Importables are the entities HTSW imports: functions, events, items, regions,
menus, NPCs, teams, groups and commands. PyHTSW declares them with decorators
and class definitions; see htsw's `language/src/importjson/schemaSpec.ts`
for the underlying import.json schema.

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
- `icon` is an `Item` or `Item` subclass (optional).

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

The event name is typed to the 18 htsw events (`Player Join`, `Player Quit`,
`Player Death`, `Player Kill`, `Player Respawn`, `Group Change`,
`PvP State Change`, `Fish Caught`, `Player Enter Portal`, `Player Damage`,
`Player Block Break`, `Start Parkour`, `Complete Parkour`, `Player Drop Item`,
`Player Pick Up Item`, `Player Change Held Item`, `Player Toggle Sneak`,
`Player Toggle Flight`).

## Items, Regions, NPCs, Menus

These are declared as **subclasses** via `__init_subclass__`: the underlying
constructor arguments are passed as class keyword arguments. Defining the class
registers the importable. `Item` and `Region` use the class name as their htsw
name; `NPC` and `Menu` take a **required `name=`** keyword argument instead, so
the displayed name can differ from the Python class name. An `NPC` name may use
formatting codes; a `Menu` title may **not** — codes there render literally
(e.g. `&aShop` shows as the text `&aShop`).

### Click / enter / exit handlers

Each supports both a decorator form and a keyword shorthand. Handlers are
callables that take **0 args, or 1 arg** that receives the instance.

```python
from pyhtsw import Item, chat


# Decorator form
class Wand(Item, key='blaze_rod', name='&dWand'):
    @Item.left_click
    def cast(self) -> None:
        chat('zap')

    @Item.right_click
    def block(self) -> None:
        chat('block')
```

```python
# Keyword shorthand
def cast() -> None:
    chat('zap')


class Wand(Item, key='blaze_rod', name='&dWand', on_left_click=cast):
    pass
```

The handler shorthands per importable:

| Importable | Decorators | Keyword shorthands |
|---|---|---|
| `Item` | `@Item.left_click`, `@Item.right_click` | `on_left_click=`, `on_right_click=` |
| `Region` | `@Region.on_enter`, `@Region.on_exit` | `on_enter=`, `on_exit=` |
| `NPC` | `@NPC.left_click`, `@NPC.right_click` | `on_left_click=`, `on_right_click=` |

### Region

```python
from pyhtsw import Region, chat


class SpawnZone(Region, bounds=((0, 60, 0), (16, 80, 16))):
    @Region.on_enter
    def entered(self) -> None:
        chat('&aentered spawn')

    @Region.on_exit
    def left(self) -> None:
        chat('&7left spawn')
```

`bounds` is `((x, y, z), (x, y, z))` — the from/to corners.

### NPC

```python
from pyhtsw import NPC, Item, chat


class Helmet(Item, key='diamond_helmet'):
    pass


class Guide(
    NPC,
    name='&bVillage Guide',
    pos=(10, 65, 10),
    skin='Steve',
    look_at_players=True,
    hide_name_tag=False,
    equipment=NPC.Equipment(helmet=Helmet),
):
    @NPC.right_click
    def talk(self) -> None:
        chat('Welcome, traveler.')
```

- `name` is **required** — the NPC's displayed name (formatting codes allowed).
- `pos` is `(x, y, z)`.
- `skin` is one of `'Steve'`, `'Alex'`, `'Players Skin'`.
- `left_click_redirect=True` makes a left click run the right-click actions.
- `NPC.Equipment(helmet=, chestplate=, leggings=, boots=, hand=)` — each is an
  `Item` or `Item` subclass.
- A handler taking one argument receives the NPC it belongs to, so it can read
  its own name and position instead of closing over them.

#### create_npc

A class statement cannot be written in a loop, so NPCs generated from data use
`create_npc`, which returns the NPC as a value. It goes anywhere a subclass does.

```python
from pyhtsw import chat, create_npc


for enemy in ENEMIES:
    def strike(enemy=enemy) -> None:
        chat(f'You strike the {enemy.name}!')

    create_npc(enemy.name, enemy.pos, skin='Steve', on_click=strike)
```

Handlers can also be attached afterwards, which reads better when there is only
one NPC and its body is long:

```python
smith = create_npc('&6Blacksmith', (10, 65, 10), look_at_players=True)


@smith.click
def forge() -> None:
    display_menu(FORGE)
```

`@npc.left_click`, `@npc.right_click` and `@npc.click` are the same names as the
class-body decorators — used on a created NPC they attach the handler, used on
the class they tag a method.

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
from pyhtsw import Menu, Item, chat, close_menu


class Filler(Item, key='gray_stained_glass_pane', name=' '):
    pass


class Confirm(Item, key='lime_dye', name='&aConfirm'):
    pass


class Shop(Menu, name='Magic Shop', size=6):
    @Menu.element(item=Filler, xy_check=lambda x, y: (x + y) % 2 == 0)
    def checkerboard(self) -> None:
        pass  # decoration only, no actions

    @Menu.element(item=Confirm, x=5, y=4)
    def confirm(self) -> None:
        close_menu()
```

- `name` is **required** — the menu's displayed title. Formatting codes are
  **not** supported here; they render literally.
- `size` is **required** and typed `Literal[1, 2, 3, 4, 5, 6]` (rows). Menus are
  9 columns wide.
- `@Menu.element(item=, slot=, x=, y=, xy_check=)`:
  - `slot` is the **flat** index Housing itself uses, `0`–`53`, shorthand for
    `x=slot // 9, y=slot % 9`. It also takes a sequence of indices. Pass either
    `slot=` or `x=`/`y=`, never both.
  - `x` is the **row**, `y` is the **column**. Each is `int | Sequence[int] |
    None`; `None` means every index on that axis.
  - Negative indices are allowed and resolved against the size at render time.
  - `xy_check=lambda x, y: ...` filters cells (e.g. a checkerboard pattern).
  - An element body of just `pass` is decoration (no actions).
- Later elements override earlier ones per cell. Overriding a cell that a
  fully-explicit element (both `x` and `y` given) already set logs a warning.

#### Menus as values

A class statement cannot be written in a loop, so a menu built from data — one
page per shop category, one per reward tier — is declared with `create_menu`
instead. It returns a `Menu` that goes anywhere a `Menu` subclass does,
`display_menu` included, and because the whole menu is built inside an ordinary
function, its handlers close over the loop variable normally rather than having
to capture it in a default argument.

```python
from pyhtsw import Menu, create_menu, give_item


def build_page(category) -> Menu:
    menu = create_menu(f'Shop > {category.name}', 6)
    menu.fill(Black, xy_check=lambda x, y: menu.distance_from_edge(x, y) == 0)
    menu.fill(Gray, xy_check=lambda x, y: menu.distance_from_edge(x, y) == 1)
    menu.place(INFO_ITEM, slot=4)

    for slot, entry in zip(SLOTS, category.items, strict=True):

        @menu.on(item=entry.item, slot=slot)
        def _buy(entry=entry) -> None:
            give_item(entry.item)

    return menu


PAGES = [build_page(category) for category in CATEGORIES]
```

- `menu.place(item, slot=/x=/y=/xy_check=)` puts an item down with **no actions
  behind it** — decoration, or a label. It saves writing a handler whose whole
  body is `pass`.
- `menu.fill(item, xy_check=)` places `item` in every cell the check accepts
  (every cell when it is omitted). Later placements win, so fill first.
- `menu.on(item=, slot=, ...)` is the decorator form; `menu.add_element(...)` is
  the same method under its original name.
- `menu.distance_from_edge(x, y)` is how many cells in from the nearest border a
  cell is — `0` on the outer ring, `1` on the next — which is what makes the
  two-tone glass border above one line each.

Note the loop above still binds `entry` through a default argument, because the
`for` body is not its own scope; lifting the loop into a helper that returns the
handler, or building one menu per function call, removes even that.

All of these are available on a `Menu` subclass too, where `place`, `fill`, `on`
and `distance_from_edge` bind to the class.

## Teams and Groups

Teams and groups hold no actions, so they are declared with factory functions
rather than classes. Each returns the same `Team` / `Group` value the actions
already take, so a declared team is used exactly like an undeclared one.

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

Every declared field reads back off the value itself — `VIP.priority`,
`VIP.color`, `Red.friendly_fire` — including through a bare `Group('VIP')`,
since that compares equal to the declared one. A field left out of the
declaration reads as `None`; `permissions` comes back as a read-only view.
Reading a name that was never declared in the current container raises, rather
than answering `None` for a group that does not exist here:

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
