# PyHTSW

PyHTSW is a Python DSL that compiles to [HTSW](https://github.com/LGHousing/htsw) projects, created to simplify the process of making housings on [Hypixel](https://hypixel.net/).

You write your house in Python: its functions, items, events, menus, commands and NPCs. Running your script compiles the whole thing into a complete HTSW project: an `import.json`, the `.htsl` files it references and the `.snbt` items they use. Import the project with HTSW and you're all set!

## Prerequisites

- [HTSW](https://github.com/LGHousing/htsw)
- [Python](https://www.python.org/) 3.13 or newer

## Installation

Make sure Git is available in your system's PATH, then run:

```bash
pip install "git+https://github.com/69Jesse/pyhtsw.git" --upgrade
```

## Usage

Imagine we have a file called `experience.py`:

```python
from pyhtsw import *

experience = PlayerStat('experience')
reward = PlayerStat('reward')
multiplier = PlayerStat('multiplier')
global_multiplier = GlobalStat('multiplier')
level = PlayerStat('level')
EXP_TO_LEVEL_UP = 100


@function('Add EXP & Level Up')
def level_up() -> None:
    experience.value += reward * multiplier * global_multiplier
    chat(f'&aYour EXP has been updated to &6{experience}g')

    with IfAll(experience >= EXP_TO_LEVEL_UP):
        experience.value -= EXP_TO_LEVEL_UP
        level.value += 1
        chat(f'&eYou leveled up to &dLevel {level}&e!')
    with Else:
        chat(f'&eOnly &a{EXP_TO_LEVEL_UP - experience} EXP&e left to level up!')
```

Run it like any other Python file:

```bash
python experience.py
```

That writes a project folder named `experience` into your HTSW projects folder:

```
experience/
├── import.json
└── functions/
    └── add-exp-level-up.htsl
```

`import.json`:

```json
{
  "functions": [
    {
      "name": "Add EXP & Level Up",
      "actions": "functions/add-exp-level-up.htsl"
    }
  ]
}
```

`functions/add-exp-level-up.htsl`:

```kotlin
// Generated with PyHTSW (https://github.com/69Jesse/pyhtsw)
var "tmp0" = %var.player/reward% false
var "tmp0" *= %var.player/multiplier% false
var "tmp0" *= %var.global/multiplier% false
var "experience" += %var.player/tmp0% true
chat "&aYour EXP has been updated to &6%var.player/experience%g"
if and (var "experience" >= 100) {
    var "experience" -= 100 true
    var "level" += 1 true
    chat "&eYou leveled up to &dLevel %var.player/level%&e!"
} else {
    var "tmp0" = 100 false
    var "tmp0" -= "%var.player/experience 0%L" false
    chat "&eOnly &a%var.player/tmp0 0% EXP&e left to level up!"
}
```

## Importables

The example above is a function. Everything else HTSW imports is declared the same way: functions, events and commands are decorators; items, menus, regions, NPCs, teams and groups are classes.

### Item

```python
book = Item(
    'enchanted_book',
    name='&dLevel Up Book',
    on_right_click=lambda: trigger_function(level_up),
)
```

### Event

```python
@event('player_join')
def on_join() -> None:
    chat(f'&aWelcome back, &6{PlayerName}!')
```

### Menu

```python
levels = Menu('Levels', 1)


@levels.add_element(Item('emerald', name='&aLevel Up'), slot=4)
def level_up_slot() -> None:
    trigger_function(level_up)
```

### Command

```python
@command('level')
def level_command() -> None:
    chat(f'&eYou are &6Level {level}&e.')
```

### NPC

```python
NPC('&bLevel Master', (10, 65, 10), on_click=lambda: display_menu(levels))
```

## Documentation

[`docs/`](docs/) has the rest: what you can [declare](docs/importables.md), how [expressions](docs/expressions.md) turn into HTSL, what the [optimizer](docs/optimizer.md) rewrites, and how to [test a house in Python](docs/emulation.md) before you import it.
