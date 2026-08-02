from pyhtsw import (
    Container,
    HasPermission,
    IfAll,
    PlayerStat,
    chat,
    create_event,
    create_function,
    full_heal,
)

# A function block splits into an overflow function once 25 conditionals are
# used; an event block fits 40 of them.
COND = 30


def build(n: int) -> None:
    for i in range(n):
        with IfAll(PlayerStat('x') > i):
            chat('hi')


with Container() as as_function:

    @create_function('Many')
    def _many() -> None:
        build(COND)


function_blocks = [b for b in as_function.blocks if not b.is_empty()]
assert len(function_blocks) > 1, (
    f'expected {COND} conditionals to overflow a function block, '
    f'got {len(function_blocks)} block(s)'
)

with Container() as as_event:

    @create_event('Player Join')
    def _on_join() -> None:
        build(COND)


event_blocks = [b for b in as_event.blocks if not b.is_empty()]
assert len(event_blocks) == 1, (
    f'expected {COND} conditionals to fit one event block (limit 40), '
    f'got {len(event_blocks)} blocks'
)


# Inside a Random, a limit below 10 is raised to 10. full_heal is 5 normally.
from pyhtsw.actions.full_heal import FullHealExpression  # noqa: E402
from pyhtsw.limits import get_limit  # noqa: E402

assert get_limit(FullHealExpression) == 5
assert get_limit(FullHealExpression, nested='random') == 10
assert get_limit(FullHealExpression, nested='conditional') == 5


# Eight full_heals fit inside a random but not at block level.
from pyhtsw.limits import Counter  # noqa: E402

block_counter = Counter()
random_counter = Counter(nested='random')
for _ in range(8):
    expression = FullHealExpression()
    if not random_counter.would_exceed(expression):
        random_counter.increment(expression)
assert sum(random_counter.count.values()) == 8, random_counter.count
fitted = 0
for _ in range(8):
    expression = FullHealExpression()
    if block_counter.would_exceed(expression):
        break
    block_counter.increment(expression)
    fitted += 1
assert fitted == 5, fitted


# More than 20 of one condition type in a single conditional is an error.
raised = False
try:
    with Container():

        @create_function('TooMany')
        def _too_many() -> None:
            with IfAll(*[HasPermission('Fly') for _ in range(21)]):
                chat('hi')
except RuntimeError as exc:
    raised = 'exceeds the limit of 20' in str(exc)
assert raised, 'expected a RuntimeError for 21 hasPermission conditions'


# 20 is still fine, and so is a mix that stays under each type's own limit.
with Container():

    @create_function('JustEnough')
    def _just_enough() -> None:
        with IfAll(
            *[HasPermission('Fly') for _ in range(20)],
            *[PlayerStat('x') > i for i in range(20)],
        ):
            chat('hi')


# full_heal keeps working normally at block level.
with Container() as plain:
    full_heal()
assert plain.into_htsl() == 'fullHeal'
