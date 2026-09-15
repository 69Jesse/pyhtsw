from pyhtsw import (
    ActionLimitError,
    Container,
    Else,
    IfAll,
    PlayerPositionX,
    PlayerStat,
    Random,
    chat,
    function,
)
from pyhtsw.compiler.limits import Counter
from pyhtsw.expression.condition.conditional_expression import ConditionalExpression

# `x = (pos - last) * 20 / ticks` flattens to 7 CHANGE_VARs and renders as 4
# once the temps merge. The limit counter has to measure the rendered number:
# counting the raw flatten budgeted a real 17-action else branch at 26.
x = PlayerStat('p/v/x').as_double()
last_x = PlayerStat('p/v/last_x').as_double()
ticks = PlayerStat('p/v/ticks').as_long()

with Container(ignore_action_limits=True) as measured:

    @function('Measured')
    def _measured() -> None:
        x.value = (PlayerPositionX - last_x) * 20 / ticks


block = next(b for b in measured.blocks if b.get_name() == 'Measured')
counts = Counter().keyed_counts(block.expressions[0])
assert counts == {'CHANGE_VAR': 4}, counts


def velocity() -> None:
    for axis in 'xyz':
        vel = PlayerStat(f'p/v/{axis}').as_double()
        last = PlayerStat(f'p/v/last_{axis}').as_double()
        vel.value = (PlayerPositionX - last) * 20 / ticks
        last.value = PlayerPositionX
    ticks.unset()
    PlayerStat('p/v/unchanged').unset()


# The reported shape: 17 rendered actions in an else branch, which nothing
# can split, so an overcount is a hard error rather than a spare wrapper.
with Container() as in_branch:

    @function('Velocity')
    def _velocity() -> None:
        with IfAll(ticks > 0):
            ticks.value += 1
        with Else:
            velocity()


htsl = in_branch.into_htsl()
assert htsl.count('\n    var ') == 18, htsl
assert htsl.count('\nif') == 0, htsl


# At the top level the same overcount cost a spurious wrapper conditional.
with Container() as top_level:

    @function('Top')
    def _top() -> None:
        for i in range(4):
            last = PlayerStat(f'p/l{i}').as_double()
            PlayerStat(f'p/s{i}').as_double().value = (
                (PlayerPositionX - last) * 20 / ticks
            )


block = next(b for b in top_level.blocks if b.get_name() == 'Top')
assert not any(isinstance(e, ConditionalExpression) for e in block.expressions), (
    block.expressions
)
assert top_level.into_htsl().count('\n') == 15, top_level.into_htsl()


# A branch that really is over reports what and where, alongside every other
# violation, instead of raising a repr dump from the middle of the fixer.
try:
    with Container():

        @function('Over')
        def _over() -> None:
            with IfAll(ticks > 0):
                ticks.value += 1
            with Else:
                for i in range(26):
                    PlayerStat(f's{i}').value += 2

        @function('Rolls')
        def _rolls() -> None:
            with Random:
                for _ in range(21):
                    chat('hi')

except ActionLimitError as error:
    message = str(error)
else:
    raise AssertionError('expected the over-limit branches to raise')

assert (
    'function "Over": 26 "CHANGE_VAR" actions in the else branch of '
    'IfAll(...) with 1 condition exceeds the limit of 25'
) in message, message
assert (
    'function "Rolls": 21 "MESSAGE" actions in the body of Random '
    'exceeds the limit of 20'
) in message, message
