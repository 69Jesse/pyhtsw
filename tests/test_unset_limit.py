from pyhtsw import Container, PlayerStat, function
from pyhtsw.compiler.limits import action_into_key, get_limit
from pyhtsw.expression.binary_expression import BinaryExpression
from pyhtsw.expression.unset_expression import UnsetExpression

# `var "x" unset` is a Change Variable to htsw, so it shares one budget with
# `var "x" = 1` rather than getting its own.
assert action_into_key(UnsetExpression) == 'CHANGE_VAR'
assert action_into_key(BinaryExpression) == 'CHANGE_VAR'
assert get_limit(UnsetExpression) == get_limit(BinaryExpression) == 25


def top_level_var_actions(htsl: str) -> int:
    depth = 0
    count = 0
    for line in htsl.splitlines():
        stripped = line.strip()
        # `} else {` closes and reopens, so net the braces rather than testing
        # for a trailing one.
        if stripped.endswith('{'):
            depth += stripped.count('{') - stripped.count('}')
            continue
        if stripped == '}':
            depth -= 1
            continue
        if depth == 0 and (
            stripped.startswith('var ') or stripped.startswith('unset var')
        ):
            count += 1
    return count


# 25 assignments plus an unset is 26 Change Variable actions, one over the cap.
with Container(ignore_scope=True) as container:

    @function('Over')
    def _over() -> None:
        for i in range(25):
            PlayerStat(f'v{i}').value = i
        PlayerStat('last').unset()


htsl = container.into_htsl()
assert top_level_var_actions(htsl) == 25, top_level_var_actions(htsl)
assert 'if and () {\n    var "last" unset\n}' in htsl, htsl

# Exactly at the cap the fixer leaves the block alone.
with Container(ignore_scope=True) as fitting:

    @function('Exact')
    def _exact() -> None:
        for i in range(24):
            PlayerStat(f'v{i}').value = i
        PlayerStat('last').unset()


htsl = fitting.into_htsl()
assert top_level_var_actions(htsl) == 25, top_level_var_actions(htsl)
assert 'if and ()' not in htsl, htsl
