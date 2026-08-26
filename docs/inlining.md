# Inlining

Two budgets shape how a house is written, and they pull in opposite directions.

A house may hold **200 functions**, house-wide, shared by every feature, with no
way to buy more. A single **action list** — a function body, a command, one menu
slot, one region's enter block, one branch of a conditional — is capped at a few
dozen actions of each kind, and when a block runs over, PyHTSW spends a wrapper
or a follow-up function to buy more room (see [Optimizer](./optimizer.md)).

So actions are cheap and functions are scarce. Spend a function only when it
buys something.

## Menus and commands: inline

A menu slot and a command each own an action list of their own. A slot whose
whole body is `triggerFunction Open Bank` costs a function *and* the action that
calls it, in exchange for nothing: nobody else triggers that function, and the
actions would have fit in the slot.

```python
# Wasteful: a function nobody else triggers.
@function('Open Bank')
def open_bank() -> None:
    display_menu(BANK_MENU)
    play_sound('random.click')


@menu.add_element(BANK_ICON, slot=20)
def _bank() -> None:
    trigger_function(open_bank)


# Inline: the same behaviour, one fewer function.
@menu.add_element(BANK_ICON, slot=20)
def _bank() -> None:
    display_menu(BANK_MENU)
    play_sound('random.click')
```

Sharing in Python is not sharing in Housing. A plain helper called from ten
slots writes its actions into all ten lists and costs no function at all, so
factoring a common body out is free:

```python
def open_menu(menu: 'Menu | str') -> None:
    display_menu(menu)
    play_sound('random.click')
```

Reach for a real function when the actions have to be genuinely *one* thing:
several callers must run the same list rather than a copy of it, a loop
(`repeat_ticks`) needs somewhere to live, the body is too big for one list
anyway — or it is an item's behaviour.

## Items: never inline

Items are the exception, and the reason has nothing to do with budget.

When Housing imports an item that has click actions, it binds them to the item
through an `ExtraAttributes.interact_data` tag. htsw manages that tag: you never
write one, and `htsw check` rejects source NBT that carries one. Every copy of
the item that has been handed out carries the binding it was given, and there is
no way to re-bind the copies already sitting in inventories, ender chests and
other people's trades.

So an item's own action list should be the part that never has to change:

```python
@function('Teleport To Crown', icon=Item('compass'))
def teleport_to_crown() -> None:
    ...


CROWN_COMPASS: Item = Item(
    'compass',
    name='&6Crown Compass&7 (Right Click)',
    on_right_click=lambda: trigger_function(teleport_to_crown),
)
```

The behaviour now lives somewhere still editable. Re-import `Teleport To Crown`
and every compass ever handed out — including the ones you will never see
again — does the new thing. Inline the same actions on the item instead and the
only way to change them is to find every copy.

This holds even for behaviour that will obviously never change. One function
buys the ability to fix, nerf or disable an item that is already in circulation,
which is not a thing you can decide you need later.

### Except `consumeItem`

`consumeItem` consumes *the item that was clicked*, so it only means anything in
the item's own action list — a function has no item in hand. A consumable
ability item is therefore exactly two inline actions:

```python
def _use() -> None:
    consume_item()
    trigger_function(cast_fireball)


FIREBALL: Item = Item('fire_charge', name='&cFireball', on_right_click=_use)
```

Keep the inline half to those two. Anything that prints, plays or moves belongs
on the far side of the `trigger_function`.
