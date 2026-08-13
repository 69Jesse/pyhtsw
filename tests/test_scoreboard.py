import warnings

from helpers import expect_exception

from pyhtsw.ext import (
    fix_scoreboard_line,
    number_lengths,
    remove_formatting,
    simulate_hypixel_split,
)

# (line, prefix, suffix, dropped, gap)
OBSERVED: tuple[tuple[str, str, str, str, bool], ...] = (
    # Hypixel's own header and footer: plain cut, colors reapplied.
    ('&ewww.hypixel.net', '§ewww.hypixel.ne', '§et', '', False),
    ('&708/13/26 m182AQ ', '§708/13/26 m182A', '§7Q ', '', False),
    # Bold, cut mid-run: the emoji inherits bold and opens the gap.
    ('&1&l123456789012345', '§1§l123456789012', '§1§l345', '', True),
    # A color code landing on the seam clears bold -- no gap. Note the
    # remainder starts with `§l`, which does not suppress the reapply.
    ('&6&l1234567890&6&l12345', '§6§l1234567890§6', '§6§l12345', '', False),
    # Index 15 is `§`, so the cut backs off to 15 and the emoji stays bold.
    ('&3&l12345678901&3&l2345', '§3§l12345678901', '§3§l2345', '', True),
    # T1: the reapplied `§4§l` is charged to the suffix, so 4 digits are lost.
    (
        '&4&l1234567890123456789012345678',
        '§4§l123456789012',
        '§4§l345678901234',
        '5678',
        True,
    ),
    # T2: the remainder already starts with a color, so nothing is reapplied
    # and all 12 trailing letters survive.
    (
        '&a&labcdefghijk&c&lLMNOPQRSTUVW',
        '§a§labcdefghijk',
        '§c§lLMNOPQRSTUVW',
        '',
        True,
    ),
    # T9: placeholders resolve before the cut, and Housing groups thousands.
    ('&a&l1abcdefghijklm', '§a§l1abcdefghijk', '§a§llm', '', True),
    ('&a&l1,234abcdefghijklm', '§a§l1,234abcdefg', '§a§lhijklm', '', True),
)

for line, prefix, suffix, dropped, gap in OBSERVED:
    split = simulate_hypixel_split(line)
    assert split.prefix == prefix, (line, split.prefix)
    assert split.suffix == suffix, (line, split.suffix)
    assert split.dropped == dropped, (line, split.dropped)
    assert split.has_gap is gap, (line, split.has_gap)


# a line short enough to hold no seam: the entry trails, so bold cannot show
short = simulate_hypixel_split('&a&labcdefgh')
assert short.suffix == ''
assert short.has_gap is False


def assert_safe(line: str, token: str = '', lengths: tuple[int, ...] = ()) -> None:
    for length in lengths or (0,):
        resolved = line.replace(token, 'x' * length) if token else line
        assert not simulate_hypixel_split(resolved).has_gap, (line, length)


# already safe: returned untouched
assert fix_scoreboard_line('&6&l1234567890&6&l12345') == '&6&l1234567890&6&l12345'
assert fix_scoreboard_line('&aabcdefghijklmnopqrstuvw') == '&aabcdefghijklmnopqrstuvw'


# a fresh code has to be inserted: 4 characters, landing `&1` on the seam.
# This is the same shape as the hand-written line observed above.
fixed = fix_scoreboard_line('&1&l123456789012345')
assert fixed == '&1&l1234567890&1&l12345', fixed
assert remove_formatting(fixed) == remove_formatting('&1&l123456789012345')
assert_safe(fixed)


# bold is the only code that opens a gap: underline, strikethrough, italic and
# obfuscated all leave the entry's cell alone, so those lines are left alone too
for code in 'nmok':
    untouched = f'&a&{code}abcdefghijklmnopqrst'
    assert fix_scoreboard_line(untouched) == untouched


# bold with no color of its own: uncolored scoreboard text renders white, so
# `&f` reasserts it without changing anything visible
fixed = fix_scoreboard_line('&labcdefghijklmnopqrst')
assert fixed == '&labcdefghijkl&f&lmnopqrst', fixed
assert remove_formatting(fixed) == remove_formatting('&labcdefghijklmnopqrst')
assert_safe(fixed)


# an existing color code can be nudged onto the seam instead: 2 characters
fixed = fix_scoreboard_line('&7abcdefghij&6&l1234567')
assert fixed == '&7abcdefghij&6&6&l1234567', fixed
assert remove_formatting(fixed) == remove_formatting('&7abcdefghij&6&l1234567')
assert_safe(fixed)


X = '%var.player/x%'

# the placeholder sits past the seam, so the fix goes in front of it and holds
# for every length it can take
fixed = fix_scoreboard_line(f'&a&labcdefghij{X}', {X: (1, 2, 3, 4, 5)})
assert fixed == f'&a&labcdefghij&a&l{X}', fixed
assert len(fixed) == 32
assert_safe(fixed, X, (1, 2, 3, 4, 5))

# unchanged when every declared length keeps the line inside one field
assert fix_scoreboard_line(f'&a&labc{X}', {X: (1, 2)}) == f'&a&labc{X}'

# lengths may be declared as a bare int, a range, or a Checkable
assert fix_scoreboard_line(f'&a&labcdefghij{X}', {X: range(1, 6)}) == fixed
assert fix_scoreboard_line(f'&a&labcdefghij{X}', {X: 5}) == fixed

# a placeholder that straddles the seam for some of its lengths cannot be fixed
# in place, so it gets padded past the seam instead
C = '%var.player/c%'
COINS = number_lengths(0, 999_999)
fixed = fix_scoreboard_line(f'&6&lCoins: {C}', {C: COINS})
assert fixed == f'&6&lCoins: &l&6&l{C}', fixed
assert remove_formatting(fixed) == remove_formatting(f'&6&lCoins: {C}')
assert_safe(fixed, C, COINS)

# a longer variable name only costs source characters, which are cheap
LONG = '%var.player/coins%'
fixed = fix_scoreboard_line(f'&6&lCoins: {LONG}', {LONG: COINS})
assert fixed == f'&6&lCoins: &l&6&l{LONG}', fixed
assert_safe(fixed, LONG, COINS)

# T9's line: the seam falls inside the placeholder for some of its lengths, so
# the placeholder is padded past the seam entirely. The padding pushes its tail
# off the screen, which is warned about (covered below) rather than refused.
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    fixed = fix_scoreboard_line(f'&a&l{X}abcdefghijklm', {X: (1, 5)})
    # a dirty placeholder takes the same fix: with the seam ahead of it, what
    # it resolves to no longer matters
    same = fix_scoreboard_line(f'&a&l{X}abcdefghijklm', {X: (1, 5)}, dirty=[X])
assert fixed == f'&a&l&l&l&l&l&l&a&l{X}abcdefghijklm', fixed
assert remove_formatting(fixed) == remove_formatting(f'&a&l{X}abcdefghijklm')
assert_safe(fixed, X, (1, 5))
assert same == fixed


# a line written by hand in game, whose fix was confirmed to close the gap
HOUSE = '%house.players%'
line = f'&4htsw &lHUMANITY&a {HOUSE}✌'
assert simulate_hypixel_split(line.replace(HOUSE, '1')).has_gap
fixed = fix_scoreboard_line(line, {HOUSE: (1, 2, 3)})
assert fixed == f'&4htsw &lHUMAN&4&lITY&a {HOUSE}✌', fixed
assert remove_formatting(fixed) == remove_formatting(line)
assert_safe(fixed, HOUSE, (1, 2, 3))


# an undeclared placeholder is never guessed at
with expect_exception(ValueError):
    fix_scoreboard_line(f'&a&labcdefghij{X}')


# the styling behind a dirty placeholder is unknowable, so the seam is only
# allowed past a point where the codes have been reasserted
fixed = fix_scoreboard_line(f'&a&l{X}abcdefg', {X: (6, 7)}, dirty=[X])
assert fixed == f'&a&l{X}abc&a&ldefg', fixed
assert remove_formatting(fixed) == remove_formatting(f'&a&l{X}abcdefg')


# T1's line: fixable, but 4 of its digits never reach the screen
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter('always')
    fixed = fix_scoreboard_line('&4&l1234567890123456789012345678')
assert fixed == '&4&l1234567890&4&l123456789012345678', fixed
assert len(caught) == 1, caught
assert 'cut off in game' in str(caught[0].message)

# past the longest source length observed to work in game, the result is
# flagged rather than refused -- the editor's own cap has never been measured
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter('always')
    fixed = fix_scoreboard_line(f'&a&l{X}abcdefghijklmno', {X: (1, 5)})
assert len(fixed) == 47
assert any('are known to be accepted in game' in str(c.message) for c in caught)


assert number_lengths(0, 9) == (1,)
assert number_lengths(0, 999) == (1, 2, 3)
# 1234 renders as "1,234"
assert number_lengths(0, 9999) == (1, 2, 3, 5)
assert number_lengths(1000, 9999) == (5,)
assert number_lengths(0, 9999, group=False) == (1, 2, 3, 4)
# the sign only applies to magnitudes that are actually negative
assert number_lengths(-9, 999) == (1, 2, 3)
assert number_lengths(-999, -100) == (4,)
assert number_lengths(0, 99, decimals=3) == (5, 6)

with expect_exception(ValueError):
    number_lengths(10, 1)
