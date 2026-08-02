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

- `repeat_ticks` runs the function on an interval (optional).
- `icon` is an `Item` or `Item` subclass (optional).

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
- `@Menu.element(item=, x=, y=, xy_check=)`:
  - `x` is the **row**, `y` is the **column**. Each is `int | Sequence[int] |
    None`; `None` means every index on that axis.
  - Negative indices are allowed and resolved against the size at render time.
  - `xy_check=lambda x, y: ...` filters cells (e.g. a checkerboard pattern).
  - An element body of just `pass` is decoration (no actions).
- Later elements override earlier ones per cell. Overriding a cell that a
  fully-explicit element (both `x` and `y` given) already set logs a warning.

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
