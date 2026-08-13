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

## Length

What renders is capped at 16 + 16 characters of *resolved* text, reapplied
codes included. What the editor accepts as *source* is a separate question, and
the answer is: more than you are likely to need. A 45-character line of nothing
but placeholder tokens comes through whole, and the 40-character output of a
fix is accepted.

The two are easy to conflate, because source and resolved length are usually
close and then a source cap and the render cap predict the same output. They
come apart when a placeholder is involved -- a token is long in source and
short once resolved:

```
&4htsw &lHUMANITY&a %house.players%✌      36 characters of source
§4htsw §lHUMANITY§a 1✌                    22 once resolved, comfortably inside
```

So `fix_scoreboard_line` enforces no source limit. Beyond
`KNOWN_GOOD_SOURCE_LENGTH` -- the longest line actually observed to survive --
it warns rather than refuses, since the real cap has never been measured and
guessing at one would reject lines Housing accepts. It also warns when the
render caps cut visible text off, which is the limit that genuinely bites.

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

Source characters are cheap; the 16-character prefix is the scarce resource.

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
the seam entirely, which is what the padding in the example above does. That
costs more source characters than the usual 4, but source characters are the
cheap resource; what it really costs is the visible text the padding displaces
out of the prefix, which is what the truncation warning reports.

Pass a placeholder in `dirty` when it can resolve to text that itself contains
color codes. The styling behind it is then unknowable, so the seam is only
allowed to land somewhere the codes have since been reasserted.

## Where this came from

None of the above is documented by Hypixel. It was reverse-engineered by
putting lines on a scoreboard and reading back what rendered, so every rule
traces to a specific observation:

| line entered | what it established |
| --- | --- |
| Hypixel's own `www.hypixel.net` and date lines | the cut at 16, and that colors are reapplied after it |
| `&1&l123456789012345` | a bold seam opens the gap |
| `&6&l1234567890&6&l12345` | a color code on the seam closes it -- and a remainder starting `§l` does *not* suppress the reapply |
| `&3&l12345678901&3&l2345` | the cut backs off to 15 rather than splitting a code pair |
| `&4&l1234567890123456789012345678` | only 24 of 28 digits render: the reapplied codes are charged to the suffix, and truncation happens after they are prepended |
| `&a&labcdefghijk&c&lLMNOPQRSTUVW` | all 12 trailing letters render: the reapply is skipped when the remainder already starts with a color |
| `&a&l%var.player/x%abcdefghijklm`, with x at 1 and 1234 | the seam moves four letters, not three: placeholders resolve before the cut, and Housing groups thousands |
| the same runs under `&n`, `&m`, `&o` and `&k` | no artifacts -- bold is the only code that matters |
| `&labcdefgh&fijklmnop` | uncolored text is white, so `&f` is a safe reassertion |
| `%house.players%` three times over, 45 characters | no source truncation at 45 |
| `&4htsw &lHUMAN&4&lITY&a %house.players%✌` | a generated fix closing a real gap in game |

The last one is the end-to-end check: `fix_scoreboard_line` produces exactly
that line from the unfixed original, and the gap it predicted was there before
and gone after.
