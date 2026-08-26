from pyhtsw import (
    Container,
    Else,
    IfAll,
    IfAny,
    NoOptimization,
    PlayerStat,
    chat,
    exit_function,
    function,
    pause_execution,
)

x = PlayerStat('x').as_long()
y = PlayerStat('y').as_long()
z = PlayerStat('z').as_long()


def htsl_of(body: 'object', name: str = 'merge') -> str:
    with Container() as container:
        function(name)(body)  # type: ignore[arg-type]
    return next(
        block.into_htsl() for block in container.blocks if block.get_name() == name
    )


def conditionals(htsl: str) -> int:
    return htsl.count('if and (') + htsl.count('if or (')


# Same check, bodies that leave the check alone: merged.
def mergeable() -> None:
    with IfAll(x > 5):
        y.value += 1
    with IfAll(x > 5):
        chat('hi')


merged = htsl_of(mergeable)
assert conditionals(merged) == 1, merged
assert merged.index('var "y" += 1') < merged.index('chat "hi"'), merged


# Conditions given in a different order are the same check.
def reordered_conditions() -> None:
    with IfAll(x > 5, y > 1):
        z.value += 1
    with IfAll(y > 1, x > 5):
        z.value += 2


assert conditionals(htsl_of(reordered_conditions)) == 1, htsl_of(reordered_conditions)


# The first body writes a stat the condition reads, so the second check could
# come out differently; these must stay apart.
def flips_its_own_check() -> None:
    with IfAll(y > 1):
        y.value += 5
    with IfAll(y > 1):
        z.value += 1


assert conditionals(htsl_of(flips_its_own_check)) == 2, htsl_of(flips_its_own_check)


# A barrier in the first body means everything about the second check is out of
# reach, including whether it still holds.
def barrier_body() -> None:
    with IfAll(x > 5):
        pause_execution(1)
    with IfAll(x > 5):
        z.value += 1


assert conditionals(htsl_of(barrier_body)) == 2, htsl_of(barrier_body)


# `exit` in the first body means the second one may never be reached at all.
def exiting_body() -> None:
    with IfAll(x > 5):
        exit_function()
    with IfAll(x > 5):
        z.value += 1


assert conditionals(htsl_of(exiting_body)) == 2, htsl_of(exiting_body)


# Different modes are different checks even with identical condition lists.
def different_modes() -> None:
    with IfAll(x > 5, y > 1):
        z.value += 1
    with IfAny(x > 5, y > 1):
        z.value += 2


assert conditionals(htsl_of(different_modes)) == 2, htsl_of(different_modes)


# Else branches merge alongside their if branches.
def with_else() -> None:
    with IfAll(x > 5):
        z.value += 1
    with Else:
        z.value += 10
    with IfAll(x > 5):
        z.value += 2
    with Else:
        z.value += 20


both = htsl_of(with_else)
assert conditionals(both) == 1, both
assert both.count('} else {') == 1, both
# Both branches merged, and joining them put the two writes next to each other
# so the constant folder could collapse each pair.
assert 'var "z" += 3 true' in both, both
assert 'var "z" += 30 true' in both, both


# The pass is switchable on its own.
with NoOptimization(temp_merge=True, no_ops=True, fold=True, dead_stores=True):
    assert conditionals(htsl_of(mergeable)) == 2, htsl_of(mergeable)
