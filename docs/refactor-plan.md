# Structural refactor plan

Full restructure of the pyhtsw package plus an API normalization pass.
Breaking changes are allowed everywhere. Every decision below was settled
interactively; this file is the record and the execution order.

## Ground rules

- Fully type-safe: no `**kwargs: Any` factories, no `Any` at the public
  boundary. Wherever runtime introspection drives behaviour, a generated typed
  twin plus a drift test keeps the checker informed (the `gen_cloned.py`
  model).
- No narrative comments in code; rationale goes into CLAUDE.md's Architecture
  section.
- Every phase ends green: `python tests/main.py`, `ruff check && ruff format
  --check`, `python scripts/gen_cloned.py` clean, and the export path exercised
  (not just `into_htsl()` — the two render paths differ). The humanity project
  built to a temp dir is the real-world check for anything touching export
  layout.

## Decisions

### 1. Package layout — kind folders, themed modules

The 113-file flat `actions/` folder becomes:

```
pyhtsw/
  actions/        real actions only, grouped by theme (~5 modules)
    inventory.py  give_item, remove_item, drop_item, consume_item, ...
    display.py    chat, display_title, display_action_bar, display_menu, close_menu
    player.py     teleport_player, set_gamemode, full_heal, kill_player, ...
    world.py      play_sound, set_player_time, set_player_weather, ...
    flow.py       trigger_function, exit_function, pause_execution, cancel_event,
                  random, the IfAll/IfAny/Else machinery
  conditions/     ~4 themed modules after dedup
  placeholders/   player.py, server.py, house.py, date.py, random.py, team.py, group.py
  declarations/   item, menu, npc, region, team, group, function, event, command
  directives/     no_optimization, no_fallback_values, no_type_casting,
                  preserved, strict_order (one shared base, see §11)
  compiler/       schedule, simplify, limits, scope, item_plan, deferred,
                  block, container, module_export, export
  generated/      contract-v2 codegen output (see §3)
  stats/  expression/  execute/  ext/  utils/  misc/   as today
```

Exact module membership is decided during the move; the themes above are the
starting split. `types.py` dissolves into `generated/` (§3).

### 2. Registration — metadata on the class

The five hand-maintained `dict[type, ...]` tables (schedule effects, action
limits, scope names/rules, the HTSW_NAMES contract map, plus the condition
variants of each) are replaced by typed class-level declarations that
registries collect at class creation, the way placeholder `pattern=` /
`pattern_factory=` already works:

```python
@final
class GiveItemExpression(Expression):
    htsw_name = 'GIVE_ITEM'
    limit = ActionLimit(20)
    effects = Effects(writes=frozenset({Resource.INVENTORY}))
    scope = Scope(forbidden_events=('Player Quit',))
```

- One new action = one file (+ `gen_cloned.py`).
- Missing `effects` still means full barrier — safe by default, unchanged.
- `schedule.py` / `limits.py` / `scope.py` read the collected registry; their
  20–45 line lazy-import blocks die.
- The contract test iterates the registry instead of a hand-written 41-entry
  name map; a class without `htsw_name` fails CI, and the set is still
  asserted equal to htsw's.
- `ComparisonCondition`'s lhs-dependent bucketing (`COMPARE_VAR` etc.) and the
  two context-dependent limits stay as code — they are rules, not rows.
- The `__init__.py` import chain stays complete: registry collection (like
  placeholder pattern lookup via `__subclasses__()`) only sees imported
  modules.

### 3. Codegen — contract v2, data only

Extend `scripts/dump_htsw_contract.mjs` to contract v2, switched to
`--experimental-strip-types` against `language/src/**` (htsw's own generator
precedent) so it stops requiring a built `dist`; add a JSON import-attribute
resolve hook for `constants.ts`. New payload: `ACTION_SPECS`,
`CONDITION_SPECS`, `PLACEHOLDER_SPECS`, `ACTIONS_TO_KWS`/`CONDITIONS_TO_KWS`,
operator/comparison symbol maps, shorthands, and all value enums (sounds,
potions, enchantments, lobbies, gamemodes, damage causes, inventory slots,
item properties/locations/amounts, permissions, colors, chat speeds).

A new `scripts/gen_types.py` writes `pyhtsw/generated/`:

- `enums.py` — Literal unions and lookup dicts (replaces most of `types.py`)
- `specs.py` — per-action arg tables: parser order, default tails, quoting
  rule per field
- `names.py` — htsw type-name and keyword maps

Classes stay hand-written; `tests/test_htsw_contract.py` grows checks that
every action's rendering agrees with `specs.py` (arg order, default-tail
filling, quoting rule).

Facts the generator must respect (verified against htsw source):

- `ACTION_SPECS` is advisory upstream (only the VS Code extension reads it) —
  the dumper adds drift assertions: spec keywords vs `ACTION_KWS` vs an actual
  round-trip parse.
- `balanceTeam` exists in the spec tables but has no parse branch — excluded.
- Argument order comes from `ACTION_SPECS` / the printer, never from the AST
  type declarations (`dropItem` proves they disagree).
- The var-family conditions (6 keywords → `COMPARE_VAR`) have no spec rows and
  stay hand-modelled.
- Placeholders carry no assignability flag upstream; pyhtsw keeps modelling it.
- Optional args are positional and unskippable — `defaultTailFor`, the `title`
  fadein/stay/fadeout grouping and the `applyPotion` level/override grouping
  become table data in `specs.py`.
- Three quoting rules (`quoteString` / `quoteName` /
  `quoteStringOrPlaceholder`) become a per-field enum in `specs.py`;
  underscore-cased enum options are the canonical emission form.

### 4. equals / __repr__ — derived at runtime

`BaseObject` implements both generically from `__clone_fields__` (already
computed by `__init_subclass__`): `equals` compares exact type then every
clone field via `equals_or_eq`; `__repr__` renders `Cls<field=..., ...>`.
~100 hand-written methods are deleted. The four genuinely custom
implementations stay as overrides (`ConditionalExpression`,
`ComparisonCondition`, `Block`, `AssertExecutionExpression`), plus any whose
clone fields do not capture equality-relevant state (`__clone_extra__`
carriers are included in the comparison where semantics require it —
`Condition.inverted` in particular). `gen_cloned.py` drops its
equals/`__repr__` anchors.

### 5. Exports — everything stays, plus every type alias

Top level keeps all classes (action expressions, conditions, placeholders,
bases) for annotation use. Removed only: confirmed-dead names, the duplicate
condition pairs (§7), superseded `Location` subclasses (`CurrentLocation`,
`CustomLocation`, `HouseSpawnLocation`, `InvokersLocation`),
`cheap_read`/`cheap_write`, `Layout`, and the second spelling of each
directive (§11). Added: every Literal alias under its new PascalCase name
(§8). `__init__.py` stays hand-written redundant-alias form (it is
load-bearing for registry collection) but is regrouped to mirror the new
package layout.

### 6. Declarations — constructors declare, decorators for callback kinds

- Value kinds are declared by their class: `Item(...)`, `Menu(...)`,
  `Region(...)`, `NPC(...)`, `Team(...)`, `Group(...)`. `Team` and `Group`
  now register like the rest.
- The three single-action-list kinds are decorators, renamed without the
  prefix: `@function('Greet')`, `@event('Player Join')`,
  `@command('spawn')`.
- All `create_*` forms are removed, including the pure aliases
  (`create_region`, `create_menu`) and the untyped `create_item`
  (`**fields: Any` dies; `Item.__init__`'s explicit typed parameter list is
  the one signature).
- `Function` / `Event` / `Command` are not publicly constructible; the types
  stay exported for annotations. The decorated `Function` value remains
  callable in scripts (emits the trigger, as today).
- Reference rule, uniform: **the class declares, the string refers.** Every
  consumer accepts `Declared | str` (`TeamStat('kills', 'Red')`,
  `set_player_team('Red')`, `trigger_function('greet')`,
  `change_player_group('VIP')`, `HasTeam('Red')`, ...). Undeclared
  teams/groups/functions that already exist in the house are reached by
  string only.
- NPC/Item/Region/Menu handler attachment unified on `on_*`: constructor
  kwargs (`on_click`, `on_left_click`, `on_right_click`, `on_enter`,
  `on_exit`) and decorator forms (`@npc.on_click`, `@item.on_right_click`,
  `@region.on_enter`) share names. The Menu slot API is consolidated around
  one placement method family with `item` in one consistent position; the
  `on` alias dies. The duplicated overload/conflict machinery
  (`_reject_click_conflict` / `_resolve_click_handlers`) merges into one
  helper.

### 7. Conditions — Is*/Has* + bare event nouns

- Duplicate pairs deleted: `PlayerFlying`, `PlayerSneaking`,
  `DoingParkour` (keeping `IsFlying`, `IsSneaking`, `IsDoingParkour`).
- `Required*` dies: `RequiredGroup` → `HasGroup`, `RequiredTeam` → `HasTeam`,
  `RequiredGamemode` → `IsGamemode`.
- Player-state checks: `Is*` / `Has*` (`IsSneaking`, `IsFlying`,
  `IsDoingParkour`, `IsItem`, `IsGamemode`, `HasItem`, `HasPermission`,
  `HasPotionEffect`, `HasGroup`, `HasTeam`, `CanPVP`). Event-context checks
  keep their bare noun (`DamageCause`, `DamageAmount`, `PortalType`,
  `FishingEnvironment`, `BlockType`). `WithinRegion` stays.
- `HasItem`/`IsItem` `required_amount` rendering unified (one mapping, one
  quoting); `IsItem` drops the meaningless `crafting_grid` option.
- `DamageAmount`'s operator-overload singleton is kept but re-typed so the
  `__eq__` override hazard is contained (documented as the one comparison-shaped
  condition).

### 8. Enums — Literal aliases, PascalCase names

Plain strings with Literal narrowing stay the interface. Renamed to
annotation-friendly PascalCase and all exported: `Gamemode`, `Sound`,
`PotionEffect`, `Enchantment`, `HousingColor`, `Permission`, `ChatSpeed`,
`CommandMode`, `MenuTier`, `Weather`, `PortalKind`, `InventorySlot`,
`Location` keywords, etc. (final list = every set in contract v2). Values are
normalized to htsw's canonical form with any pretty→wire mapping applied at
the render boundary; `ALL_GAMEMODES` / `ALL_DEFAULT_GAMEMODES` merge into one
`Gamemode`; one canonical sound form (raw id), the pretty→raw map applied at
the boundary; `custom_sound`'s disguised cast is replaced by an honest
`str`-accepting parameter with runtime validation. Name collisions with §7's
condition classes are resolved in the conditions' favour (`Enchantment` the
value class merges with the alias story during the move; `DamageCause` the
condition keeps its name, the value set exports as `DamageCauseName` or
similar — settled during implementation with the collision table in front of
us).

### 9. Else — unchanged

Positional `with Else:` stays exactly as it is, adjacency constraint and all.
No handle form.

### 10. Stat API bundle

- `Checkable.value` (clone-getter) is removed; `.cloned()` is the explicit
  spelling. `Editable.value` keeps the assignment idiom unchanged.
- `as_long`/`as_double`/`as_string`/`as_any` (typed views, return clones) and
  `cast_to_long`/`cast_to_double`/`cast_to_string` (emit a real cast) both
  stay, with the split documented; `as_type` is dropped.
- `with_auto_unset(flag)` absorbs `without_auto_unset()`.
- `TeamStat` becomes `(name, /, *, team=..., internal_type=...,
  fallback_value=..., auto_unset=...)` matching the family; `Team.stat`'s
  parameter renames `key` → `name`.
- `TemporaryStat`'s no-op name setter is removed (read-only property, no
  silent-ignore setter).

### 11. Directives unified

One shared base for the five flag context managers, one internal pattern
(a stack), one public spelling each. Chosen spelling: the class form used
directly — `with NoOptimization():`, `with NoFallbackValues():`,
`with NoTypeCasting():`, `with Preserved():`, `with StrictOrder():` — the
lowercase function doubles (`preserved`, `strict_order`) are removed.

### 12. Signature hygiene

- Keyword-only after the first one or two args on every action with an option
  tail (`drop_item`, `give_item`, `apply_potion_effect`, `display_title`,
  `enchant_held_item`, ...).
- `location` is the first-or-second positional where required, keyword-only
  where optional.
- `pause_execution(ticks=...)` keeps its unit visible at call sites.
- `Checkable` accepted wherever the runtime already handles it (`chat`,
  `fail_parkour`, `send_to_lobby`, title/action-bar already do).
- The stringly `*Expression` constructors stop being the shadow API: the
  public functions are the interface, expression classes exist for
  annotation and introspection.

### 13. ext / misc / config cleanup

- `ext/__init__.py`: dead aliases and the E402 tail import removed; the
  `utils/` formatting helpers (`formatting_to_ansi`, `fix_scoreboard_line`,
  `simulate_hypixel_split`, ...) move to a proper public home
  (`pyhtsw.text` or similar) instead of leaking through `ext`.
- `Stack`/`Queue`/`IntStack`/`IntQueue` get `push`/`pop` naming.
- `skulls.json` (951 KB) loads lazily on first `SKULL_DATA` access.
- `config.py`: setters normalized to one convention with symmetric exported
  getters; `should_*` naming dropped; the `input()` loop leaves
  `get_projects_folder` (raises with instructions instead); `INDENT` moves
  out of config into the render layer.
- `export.py`'s `Exportable` alias loses the `| object` that made it
  meaningless.

## Execution order

Each phase is a working state; run the full gate (tests, ruff, gen_cloned,
export-path check) before moving on.

1. **Contract v2 + generated data** (additive). Dumper rewrite, `generated/`
   package, drift tests. Nothing consumes it yet.
2. **Base machinery.** Derived `equals`/`__repr__` (delete ~100 methods);
   `ActionLimit`/`Effects`/`Scope`/`htsw_name` metadata types and registry
   collection; migrate `schedule`/`limits`/`scope`/contract-test to read the
   registry; delete the central tables. Old layout untouched — this phase is
   diffable behaviour-neutral.
3. **Folder restructure.** Move files into the §1 layout, merge themed
   modules, dissolve `types.py` into `generated/`, regroup `__init__.py`.
   Pure moves plus import updates; golden HTSL strings must not change.
4. **Declaration model + naming.** §6 decorators and constructor
   declarations, §7 condition renames and dedup, §8 Literal renames. This is
   the big breaking sweep; tests and examples updated in the same commits.
5. **Cleanup bundles.** §10 Stat API, §11 directives, §12 signatures,
   §13 ext/misc/config.
6. **Docs.** CLAUDE.md rewritten for the new layout (including its 10 stale
   `pyhtsl/` links), `docs/` and examples updated, `gen_cloned.py` re-run
   final time, humanity built to a temp dir as the closing check.
