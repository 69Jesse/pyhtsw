# Optimizer

PyHTSW rewrites what you write before emitting it, so a house imports fewer
actions and spills into fewer functions. Everything here preserves behaviour.

## Action limits

Housing caps how many of each action one container may hold. When a block runs
over, PyHTSW wraps a run of actions in a condition-less `if and () { ... }`
(which gets its own budget) or carves the tail into a follow-up function.

Because a wrapper can only hold a *run* of consecutive wrappable actions, and a
real conditional breaks the run, interleaved code pays for wrappers it does not
need. PyHTSW resequences independent expressions to avoid that:

```python
# written like this
coins.value += 1
with IfAll(coins > 5):
    coins.value += 3
gems.value += 1
with IfAll(gems > 5):
    gems.value += 3

# emitted like this once the block is full - 3 conditionals instead of 4
if and () {
    var "coins" += 1 true
    var "gems" += 1 true
}
if and (var "coins" > 5 0) { var "coins" += 3 true }
if and (var "gems" > 5 0) { var "gems" += 3 true }
```

Reordering for limits only happens when a block would otherwise overflow. A
block that fits keeps the order you wrote it in.

## What may move

Two expressions swap only when neither one's writes touch what the other reads
or writes, and they are not on the same perception stream:

- **Stats and world state.** Reads and writes are tracked per stat and per piece
  of player state (position, inventory, health, potion effects, team, …). A
  `play_sound` is emitted where the player stands, so it never moves ahead of a
  `teleport_player`.
- **Text and sound keep their order.** Chat, titles and action bars share one
  order; sounds share another. A chat and a sound may swap — within one tick you
  receive both together — but two chats never do.
- **Nothing crosses a `pause_execution`.** Other players' functions run during a
  pause and can touch the same stats.
- **`exit`, `cancel_event`, `trigger_function` and `send_to_lobby` are
  barriers**, as is any action PyHTSW does not recognise.

Expressions are also resequenced (whenever it removes actions) so that repeated
writes to one stat end up adjacent and collapse:

```python
coins.value += 8
gems.value = 3
coins.value += 8   # emitted as a single `var "coins" += 16`
```

## Merging conditionals

Adjacent conditionals checking the same thing are merged, and the joined body is
re-optimized:

```python
with IfAll(coins > 5):
    gems.value += 1
with IfAll(coins > 5):
    gems.value += 2

# becomes
if and (var "coins" > 5 0) { var "gems" += 3 true }
```

Condition order does not matter — `IfAll(a, b)` and `IfAll(b, a)` are the same
check. The merge is skipped when the first body writes something the condition
reads (it could flip the second check) or contains a barrier.

## Turning passes off

`NoOptimization` is an allow-list. A bare call disables everything; naming a
pass keeps that one running:

```python
from pyhtsw import NoOptimization

with NoOptimization():            # emitted exactly as written
    ...

with NoOptimization(fold=True):   # only constant folding still runs
    ...
```

Passes: `temp_merge`, `no_ops`, `fold`, `identity_merge`, `dead_stores`,
`reorder`, `merge_conditionals`, `dead_code`. Nested blocks intersect — a pass
runs only if every open block allows it.

## Pinning an order

If a run depends on ordering PyHTSW cannot see — an in-game side effect it does
not model, or a stat something outside PyHTSW writes — pin it:

```python
from pyhtsw import strict_order

with strict_order():
    do_this()
    then_this()
```

Nothing inside moves, and nothing from outside moves through it. The limit fixer
may still wrap the region or move it into an overflow function; neither changes
behaviour.
