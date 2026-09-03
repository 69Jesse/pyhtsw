# Scope

Housing restricts not just *how many* actions a container may hold, but *which*.
Those rules live in htsw's `checkScope` pass; PyHTSW mirrors them and raises
`ScopeError` when a container finalizes, so a house fails at build time rather
than at import.

## Items may not branch

An item's click list must be a flat run of plain actions. A `Conditional` or a
`Random` inside one is rejected:

```
ScopeError: These actions are not allowed in the container they were written into:
  - item "Record1 right": Conditional action cannot be used inside items
```

Anything that needs to branch belongs on the far side of a `trigger_function`,
which is where an item's behaviour should live anyway — see
[Inlining](./inlining.md).

```python
def _use() -> None:
    var.value = 1  # plain assignments are fine
    trigger_function(cast)  # everything that branches lives in here


FIREBALL: Item = Item('fire_charge', name='&cFireball', on_right_click=_use)
```

NPCs, regions, functions and commands are general containers and may branch
freely. Menus may too.

## The rest of the rules

| Rule | Where |
|---|---|
| `Conditional`, `Random` | not in items |
| `cancel_event` | only in a cancellable event |
| `exit_function` | only inside a conditional or random |
| `consume_item` | only in items |
| `close_menu` | only in menus |
| `kill_player`, `send_to_lobby` | never in any event |
| ~30 player-affecting actions | not in `player_quit` |
| `change_player_group` | not in `group_change` |

Cancellable events are `player_death`, `fish_caught`, `player_damage`,
`player_drop_item`, `player_pick_up_item`, `player_change_held_item`,
`player_toggle_sneak` and `player_toggle_flight`.

`player_quit` still accepts variable writes; what it refuses is everything that
acts on a player who is already gone — titles, chat, teleports, items, sounds,
health, inventory.

## Conditions scoped to one event

Some conditions only mean anything inside the event that produces the value they
read:

| Condition | Event |
|---|---|
| `DamageAmount`, `DamageCause` | `player_damage` |
| `CanPVP` | `pvp_state_change` |
| `FishingEnvironment` | `fish_caught` |
| `PortalType` | `player_enter_portal` |
| `BlockType` | `player_block_break` |
| `IsItem` | `player_drop_item`, `player_pick_up_item`, `player_change_held_item` |

## Turning it off

`Container(ignore_scope=True)` skips the pass. It exists for tests that render
HTSL for its own sake — a conditional holding `PortalType` *and* `DamageAmount`
has no legal container, but its rendering is still worth asserting on. A real
house has no reason to set it: htsw would reject the import anyway.
