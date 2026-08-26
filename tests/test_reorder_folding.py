from collections.abc import Callable

from pyhtsw import (
    Container,
    ExecutionContext,
    PlayerStat,
    chat,
    function,
    pause_execution,
)

coins = PlayerStat('coins').as_long()
gems = PlayerStat('gems').as_long()


def htsl_of(body: Callable[[], None], name: str = 'fold') -> str:
    with Container() as container:
        function(name)(body)
    return next(
        block.into_htsl() for block in container.blocks if block.get_name() == name
    )


def lines(htsl: str) -> list[str]:
    return [line.strip() for line in htsl.split('\n') if line.strip()]


# Separated writes to one stat are pulled together and folded.
def separated() -> None:
    coins.value += 8
    gems.value = 3
    coins.value += 8


assert lines(htsl_of(separated)) == [
    'var "coins" += 16 true',
    'var "gems" = 3 true',
], htsl_of(separated)


# A read of the stat in between is a real dependency: nothing may collapse.
def read_in_between() -> None:
    coins.value += 8
    gems.value = coins
    coins.value += 8


assert lines(htsl_of(read_in_between)) == [
    'var "coins" += 8 true',
    'var "gems" = "%var.player/coins 0%L" true',
    'var "coins" += 8 true',
], htsl_of(read_in_between)


# Neither may a pause be crossed to reach the fold.
def across_pause() -> None:
    coins.value += 8
    pause_execution(1)
    coins.value += 8


assert lines(htsl_of(across_pause)) == [
    'var "coins" += 8 true',
    'pause 1',
    'var "coins" += 8 true',
], htsl_of(across_pause)


# Nothing to gain here, so the source order survives untouched - a block that
# the reorder cannot improve must render exactly as it was written.
def nothing_to_gain() -> None:
    coins.value += 1
    chat('a')
    gems.value += 2
    chat('b')


assert lines(htsl_of(nothing_to_gain)) == [
    'var "coins" += 1 true',
    'chat "a"',
    'var "gems" += 2 true',
    'chat "b"',
], htsl_of(nothing_to_gain)


# A chat between the two writes reads neither stat, so it may be stepped over -
# but it stays on its own side of the other chat.
def chat_in_between() -> None:
    coins.value += 8
    chat('hello')
    coins.value += 8


folded = lines(htsl_of(chat_in_between))
assert 'var "coins" += 16 true' in folded, folded
assert 'chat "hello"' in folded, folded


# The folded program computes what the unfolded one did.
with ExecutionContext() as ctx:
    ctx.put(coins, 100, ignore_warning=True)
    ctx.put(gems, 0, ignore_warning=True)
    separated()

    def check() -> None:
        assert int(ctx.get(coins)) == 116, ctx.get(coins)
        assert int(ctx.get(gems)) == 3, ctx.get(gems)

    ctx.assert_all(check)
