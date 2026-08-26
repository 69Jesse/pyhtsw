from collections.abc import Callable

from pyhtsw import (
    Container,
    IfAll,
    NoOptimization,
    PlayerStat,
    chat,
    create_function,
    exit_function,
    strict_order,
)
from pyhtsw.directives.no_optimization import OPTIMIZATION_PASSES, optimization_enabled

a = PlayerStat('a').as_long()
b = PlayerStat('b').as_long()
fill = [PlayerStat(f'g{i}').as_long() for i in range(25)]


def htsl_of(body: Callable[[], None], name: str = 'flags') -> str:
    # Optimizer-only: one case puts `exit` at the top level of a block, which
    # htsw scopes to conditionals, so the scope pass has to stay out of the way.
    with Container(ignore_scope=True) as container:
        create_function(name)(body)
    return next(
        block.into_htsl() for block in container.blocks if block.get_name() == name
    )


def conditionals(htsl: str) -> int:
    return htsl.count('if and (') + htsl.count('if or (')


# A bare NoOptimization keeps its old meaning: nothing runs.
assert all(optimization_enabled(name) for name in OPTIMIZATION_PASSES)
with NoOptimization():
    assert not any(optimization_enabled(name) for name in OPTIMIZATION_PASSES)

# Naming a pass keeps exactly that one.
with NoOptimization(fold=True, dead_stores=True):
    assert optimization_enabled('fold')
    assert optimization_enabled('dead_stores')
    assert not optimization_enabled('reorder')
    assert not optimization_enabled('no_ops')

# Nested blocks intersect rather than replace.
with NoOptimization(fold=True, reorder=True), NoOptimization(fold=True):
    assert optimization_enabled('fold')
    assert not optimization_enabled('reorder')

assert all(optimization_enabled(name) for name in OPTIMIZATION_PASSES)

try:
    NoOptimization(nonsense=True)
except TypeError as error:
    assert 'nonsense' in str(error), error
else:
    raise AssertionError('unknown pass name should raise')


# The fold pass on its own still folds, with no other pass to help it.
def constants() -> None:
    a.value = 1
    a.value += 2


with NoOptimization(fold=True):
    assert 'var "a" = 3 true' in htsl_of(constants), htsl_of(constants)
with NoOptimization():
    assert 'var "a" = 1 true' in htsl_of(constants), htsl_of(constants)


# dead_code drops what cannot run.
def after_exit() -> None:
    chat('before')
    exit_function()
    chat('after')


assert 'chat "after"' not in htsl_of(after_exit), htsl_of(after_exit)
with NoOptimization(fold=True):
    assert 'chat "after"' in htsl_of(after_exit), htsl_of(after_exit)


# strict_order pins a region the scheduler would otherwise repack.
def loose() -> None:
    for index in range(25):
        fill[index].value = index
    a.value += 1
    with IfAll(a > 5):
        a.value += 3
    b.value += 1
    with IfAll(b > 5):
        b.value += 3


def pinned() -> None:
    for index in range(25):
        fill[index].value = index
    with strict_order():
        a.value += 1
        with IfAll(a > 5):
            a.value += 3
        b.value += 1
        with IfAll(b > 5):
            b.value += 3


assert conditionals(htsl_of(loose)) == 3, htsl_of(loose)
assert conditionals(htsl_of(pinned)) == 4, htsl_of(pinned)
# Pinned means order only - the fixer may still wrap the region's expressions.
assert 'if and () {' in htsl_of(pinned), htsl_of(pinned)
