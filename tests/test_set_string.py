from helpers import expect_exception

from pyhtsw import Container, ExecutionContext, PlayerStat
from pyhtsw.expression.binary_expression import (
    SET_STRING_MAX_LENGTH,
    BinaryExpression,
)
from pyhtsw.ext.set_string import set_string

with Container() as container:
    s = PlayerStat('s').as_string()
    set_string(s, 'hello world')

assert container.into_htsl() == 'var "s" = "hello world" true', container.into_htsl()


# value of exactly 32 chars: one line
with Container() as container:
    s = PlayerStat('s').as_string()
    value = 'A' * 32
    set_string(s, value)

assert container.into_htsl() == f'var "s" = "{value}" true', container.into_htsl()


with Container() as container:
    s = PlayerStat('s').as_string()
    # Source > 32 chars but contains a placeholder:
    # "preamble%var.player/x%suffixsuffixsuffix" = 8 + 14 + 18 = 40 chars
    value = 'preamble%var.player/x%' + 'suffixsuffixsuffix'
    assert len(value) == 40
    set_string(s, value)

htsl = container.into_htsl()
lines = htsl.split('\n')
# Every line's set-string source (the part inside double quotes) must be <= 32.
for line in lines:
    assert '"' in line, line
    src = line.split('"', 2)[1]
    assert len(src) <= SET_STRING_MAX_LENGTH, (len(src), src, line)


with expect_exception(ValueError):
    with Container() as container:
        s = PlayerStat('s').as_string()
        set_string(s, 'A' * 50)


with expect_exception(ValueError):
    with Container() as container:
        s = PlayerStat('destination').as_string()
        value = 'a' * 32 + '%var.player/y%'
        set_string(s, value)


import pyhtsw.container as _container_mod  # noqa: E402

caught = False
try:
    with Container() as container:
        s = PlayerStat('s').as_string()
        s.value = 'A' * 33
except ValueError:
    caught = True
finally:
    # If finalize raised inside Container.__exit__, the container never got
    # popped from the global stack — restore it ourselves.
    while len(_container_mod.CONTAINERS) > 1:
        _container_mod.CONTAINERS.pop()
assert caught, 'expected ValueError for >32-char direct set'


with ExecutionContext() as ctx:
    s = PlayerStat('s').as_string()
    set_string(s, 'hello')

    def check_short() -> None:
        assert str(ctx.get(s)) == 'hello', ctx.get(s)

    ctx.assert_all(check_short)


with ExecutionContext() as ctx:
    s = PlayerStat('s').as_string()
    x = PlayerStat('x').as_string()
    ctx.put(x, 'XYZ', ignore_warning=True)
    # Source 36 chars, but placeholder %var.player/x% (14 chars) substitutes
    # to "XYZ" (3 chars), so the expanded value is 36 - 14 + 3 = 25 chars,
    # well under 32. Chained self-concat should produce the right result.
    value = 'before%var.player/x%' + 'after_after_after'  # 6 + 14 + 17 = 37
    assert len(value) == 37
    set_string(s, value)
    expected = 'before' + 'XYZ' + 'after_after_after'  # 26 chars
    assert len(expected) <= SET_STRING_MAX_LENGTH

    def check_chained() -> None:
        assert str(ctx.get(s)) == expected, (ctx.get(s), expected)

    ctx.assert_all(check_chained)


with ExecutionContext() as ctx:
    a = PlayerStat('a').as_string()
    b = PlayerStat('b').as_string()
    dest = PlayerStat('dest').as_string()
    ctx.put(a, 'X' * 20, ignore_warning=True)
    ctx.put(b, 'Y' * 20, ignore_warning=True)
    # Source 28 chars (under 32 limit), but a + b = 40 chars > 32.
    dest.value = '%var.player/a%%var.player/b%'

    def check_rule_fires() -> None:
        # ctx.get_raw bypasses substitution and returns the literal source.
        raw = ctx.get_raw(dest)
        assert raw == '%var.player/a%%var.player/b%', raw

    ctx.assert_all(check_rule_fires)


with ExecutionContext() as ctx:
    a = PlayerStat('a').as_string()
    b = PlayerStat('b').as_string()
    dest = PlayerStat('dest').as_string()
    ctx.put(a, 'X' * 5, ignore_warning=True)
    ctx.put(b, 'Y' * 5, ignore_warning=True)
    # Substituted = 10 chars, well under 32, so the substituted value is stored.
    dest.value = '%var.player/a%%var.player/b%'

    def check_substituted() -> None:
        raw = ctx.get_raw(dest)
        assert raw == 'XXXXXYYYYY', raw

    ctx.assert_all(check_substituted)


with Container() as container:
    s = PlayerStat('s').as_string()
    # 3 placeholders + literals; with stat self-ref of 14 chars (1-char name),
    # continuation budget is 18 chars. Forces chunking.
    value = '%var.player/p%%var.player/q%%var.player/r%abcdefg'
    assert len(value) > SET_STRING_MAX_LENGTH
    set_string(s, value)

htsl = container.into_htsl()
chunks = htsl.split('\n')
assert len(chunks) >= 2, htsl
for line in chunks:
    src = line.split('"', 2)[1]
    assert len(src) <= SET_STRING_MAX_LENGTH, (len(src), src)


# Number of emitted BinaryExpressions for a chunked set_string equals
# number of chunks (each chunk is one Set BinaryExpression, no others).
with Container() as container:
    s = PlayerStat('s').as_string()
    value = '%var.player/p%%var.player/q%%var.player/r%abcdefg'
    set_string(s, value)

counts = container.expression_counts(nested=True)
assert BinaryExpression in counts, counts
# The exact number depends on how greedily we pack; assert the lines of HTSL
# match the BE count.
n_lines = len(container.into_htsl().split('\n'))
assert counts[BinaryExpression] == n_lines, (counts, n_lines)
