# Scoreboards

Hypixel splits every scoreboard line in two and wedges a per-line emoji into
the seam. When the seam lands on bold text the emoji inherits the bold styling,
and the font renderer's extra bold pixel opens a visible hole between two
letters. `fix_scoreboard_line` rewrites a line so that never happens.

```python
from pyhtsw.ext import fix_scoreboard_line, number_lengths

fix_scoreboard_line('&1&l123456789012345')
# '&1&l1234567890&1&l12345'
```

The result renders identically -- same visible characters, same colors, same
styling -- but the seam now falls on a color code, which clears bold.

Bold is the only code that does this. Underline, strikethrough, italic and
obfuscated all leave the entry's cell alone, so lines using them come back
untouched. A bold line carrying no color code of its own gets `&f`, since
uncolored scoreboard text renders white.

## How the split works

A line is sent as a legacy scoreboard team: a **prefix**, the **entry name**
(the emoji, whose glyph is blank in most fonts), and a **suffix**. Both fields
cap at 16 characters, `§` codes included.

```
cut = 16
if line[15] == '§':                 # never split a code pair
    cut = 15
prefix = line[:cut]
rest   = line[cut:]
if not rest.startswith(a color code or §r):
    rest = last_colors(prefix) + rest
suffix = rest[:16]
```

`last_colors` is Bukkit's `ChatColor.getLastColors`: walk backwards, collect
each code, stop at the first color or `§r`.

Three details are easy to get wrong, and all three were confirmed in game:

- **The reapplied codes are conditional.** They are skipped only when the
  remainder already begins with a *color*. A leading `§l` does not suppress
  them, because it would not restore the color.
- **They are charged to the suffix's 16 characters**, and truncation happens
  after they are prepended. A fully bold single-color line can therefore only
  ever show 24 characters: `§X§l` plus 12 in each field.
- **The cut counts `§` codes and resolved placeholders**, not visible
  characters. A var placeholder is substituted before the split, and Housing
  groups thousands -- `1234` renders as `1,234` and occupies five characters.

`simulate_hypixel_split` implements exactly this, and the test suite pins it
against every line observed in game.

## The two different caps

| cap | applies to | counts |
| --- | --- | --- |
| 32 (unconfirmed) | what the in-game editor accepts | `&` codes as 2, `%var.player/x%` as 14 |
| 16 + 16 | what renders | the resolved line, minus the reapplied codes |

They are unrelated: a 31-character line holding a placeholder can render as 60
characters and lose the tail. `fix_scoreboard_line` raises when a line exceeds
the editor's cap and warns when the render caps cut text off.

The render caps are measured and certain. The source cap is **not**: a
36-character line with a placeholder in it is accepted in game, so 32 is at
best a lower bound. It was inferred from a line whose source and resolved
lengths were nearly equal, where a source cap and the render cap predict the
same result and cannot be told apart. Until it is measured, `fix_scoreboard_line`
may refuse a line Housing would have taken.

## What the fix costs

The prefix is a fixed 16-character window, so any code inserted before the seam
displaces visible text. A fix costs **2 visible characters**, or nothing when
the seam already lands somewhere safe. In source terms it costs 4 characters
(`&X&l`), or 2 when a color code already present in the line can be nudged onto
the seam instead:

```python
fix_scoreboard_line('&7abcdefghij&6&l1234567')
# '&7abcdefghij&6&6&l1234567'
```

A line already at the editor's 32-character cap has no room for either, so it
raises -- shorten the line first.

## Placeholders

A placeholder's resolved length moves the seam, so every length it can take has
to be declared. The result is checked against all combinations of them.

```python
COINS = '%var.player/c%'

fix_scoreboard_line(f'&6&lCoins: {COINS}', {COINS: number_lengths(0, 999_999)})
# '&6&lCoins: &l&6&l%var.player/c%'
```

Lengths are what Housing *prints*, which is why `number_lengths` exists: it
accounts for the thousands separators, the sign, and optional decimals. Keys
may be the placeholder string or the `Checkable` itself. An undeclared
placeholder raises rather than being guessed at.

A placeholder that sits past the seam is free -- the fix goes in front of it.
One that straddles the seam for some of its lengths cannot be fixed in place,
since no code can be inserted inside a placeholder. It has to be pushed past
the seam instead, which is what the padding in the example above does, and that
costs more than the usual 4 characters.

This is where the editor's cap bites, because the *token* is what counts
against it: `%var.player/coins%` spends 18 of the assumed 32 characters and
`%var.player/c%` spends 14. Until that cap is measured, renaming the variable
is often the difference between a line that can be fixed and one that raises.

Pass a placeholder in `dirty` when it can resolve to text that itself contains
color codes. The styling behind it is then unknowable, so the seam is only
allowed to land somewhere the codes have since been reasserted.
