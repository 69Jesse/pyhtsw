from collections.abc import Callable

from pyhtsw import (
    Container,
    IfAll,
    NoOptimization,
    PlayerStat,
    chat,
    create_function,
    pause_execution,
)
from pyhtsw.directives.no_optimization import OPTIMIZATION_PASSES

# `NoOptimization` is an allow-list, so naming every pass but one disables
# exactly that pass - the baseline each case here is measured against.
ONLY_REORDER_OFF = {name: True for name in OPTIMIZATION_PASSES if name != 'reorder'}


def block_htsl(container: Container, name: str) -> str:
    return next(
        block.into_htsl() for block in container.blocks if block.get_name() == name
    )


def conditionals(htsl: str) -> int:
    return htsl.count('if and (') + htsl.count('if or (')


def non_empty_blocks(container: Container) -> int:
    return len([block for block in container.blocks if not block.is_empty()])


def build(name: str, body: Callable[[], None], *, reorder: bool) -> Container:
    def make() -> Container:
        with Container() as container:
            create_function(name)(body)
        return container

    if reorder:
        return make()
    with NoOptimization(**ONLY_REORDER_OFF):
        return make()


# The motivating case: with the block already full, the two independent
# `stat += 1` writes are pulled together into one wrapper instead of two.
x = PlayerStat('x').as_long()
y = PlayerStat('y').as_long()
fill = [PlayerStat(f'f{i}').as_long() for i in range(25)]


def interleaved() -> None:
    for index in range(25):
        fill[index].value = index
    x.value += 1
    with IfAll(x > 5):
        x.value += 3
    y.value += 1
    with IfAll(y > 5):
        y.value += 3


before = block_htsl(build('demo', interleaved, reorder=False), 'demo')
after = block_htsl(build('demo', interleaved, reorder=True), 'demo')

assert conditionals(before) == 4, before
assert conditionals(after) == 3, after
# Both writes ended up under the same wrapper, and each guarded write still sits
# behind its own check.
assert 'if and () {\n    var "x" += 1 true\n    var "y" += 1 true\n}' in after, after


# A dependency must survive: when the second conditional checks the stat the
# first block writes, the pair cannot be resequenced into one wrapper.
a = PlayerStat('a').as_long()
b = PlayerStat('b').as_long()


def dependent() -> None:
    for index in range(25):
        fill[index].value = index
    a.value += 1
    with IfAll(a > 5):
        b.value += 3
    b.value += 1
    with IfAll(b > 5):
        a.value += 3


dependent_after = block_htsl(build('dep', dependent, reorder=True), 'dep')
# `b += 1` reads and writes what the first conditional writes, so it stays put.
lines = [line.strip() for line in dependent_after.split('\n') if line.strip()]
assert lines.index('var "b" += 1 true') > lines.index('if and (var "a" > 5 0) {'), (
    dependent_after
)


# Nothing crosses a pause, however much packing it would buy.
def with_pause() -> None:
    for index in range(25):
        fill[index].value = index
    x.value += 1
    pause_execution(1)
    y.value += 1


paused = block_htsl(build('paused', with_pause, reorder=True), 'paused')
paused_lines = [line.strip() for line in paused.split('\n') if line.strip()]
assert paused_lines.index('var "x" += 1 true') < paused_lines.index('pause 1'), paused
assert paused_lines.index('var "y" += 1 true') > paused_lines.index('pause 1'), paused


# Two chats keep their order relative to each other even though the stat writes
# around them move.
def text_stream() -> None:
    for index in range(25):
        fill[index].value = index
    chat('first')
    x.value += 1
    with IfAll(x > 5):
        x.value += 3
    chat('second')
    y.value += 1


streamed = block_htsl(build('stream', text_stream, reorder=True), 'stream')
assert streamed.index('chat "first"') < streamed.index('chat "second"'), streamed


# Enough conditionals to overflow the 25-per-function cap: packing the wrappers
# tighter has to keep the whole thing in one function instead of spilling into
# a second one.
many = [PlayerStat(f'm{i}').as_long() for i in range(24)]


def overflowing() -> None:
    for index in range(25):
        fill[index].value = index
    for index in range(24):
        many[index].value += 1
        with IfAll(many[index] > 5):
            many[index].value += 3


spilled = build('spill', overflowing, reorder=False)
packed = build('spill', overflowing, reorder=True)
assert non_empty_blocks(packed) < non_empty_blocks(spilled), (
    non_empty_blocks(packed),
    non_empty_blocks(spilled),
)
