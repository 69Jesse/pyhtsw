from typing import Self

from pyhtsw import (
    Container,
    IfAll,
    Item,
    Location,
    PlayerStat,
    RandomWhole,
    chat,
    full_heal,
    give_item,
    pause_execution,
    play_sound,
    teleport_player,
)
from pyhtsw.compiler.schedule import Resource, Stream, build_dependencies, effects_of
from pyhtsw.expression.expression import Expression

x = PlayerStat('x').as_long()
y = PlayerStat('y').as_long()


def captured(body: 'object') -> list[Expression]:
    """The expressions a body writes, before any finalize pass touches them."""
    with Container(ignore_action_limits=True) as container:
        written = container.blocks[0].expressions
        body()  # type: ignore[operator]
        snapshot = list(written)
    return snapshot


def depends(expressions: list[Expression], later: int, earlier: int) -> bool:
    return earlier in build_dependencies(expressions)[later]


# An expression type the model has never seen is a barrier.
class MysteryExpression(Expression):
    def into_htsl(self) -> str:
        return 'mystery'

    def cloned(self) -> Self:
        return self.__class__()

    def equals(self, other: object) -> bool:
        return isinstance(other, MysteryExpression)

    def __repr__(self) -> str:
        return 'MysteryExpression'


assert effects_of(MysteryExpression()).control


# A sound is emitted where the player is standing, so a teleport before it is a
# real dependency even though no stat is involved.
sound_after_teleport = captured(
    lambda: (
        teleport_player(Location.custom(1, 2, 3)),
        play_sound('note.pling'),
    ),
)
assert depends(sound_after_teleport, 1, 0), sound_after_teleport
assert Resource.POSITION in effects_of(sound_after_teleport[0]).writes
assert Resource.POSITION in effects_of(sound_after_teleport[1]).reads


# Chat and sound are separate streams: no ordering between them by themselves.
mixed = captured(lambda: (chat('a'), play_sound('note.pling')))
assert not depends(mixed, 1, 0), mixed
assert effects_of(mixed[0]).stream is Stream.TEXT
assert effects_of(mixed[1]).stream is Stream.SOUND

# Two chats are on one stream and never swap.
two_chats = captured(lambda: (chat('a'), chat('b')))
assert depends(two_chats, 1, 0), two_chats


# Reading a value that changes on every read pins the reads in order.
def volatile() -> None:
    x.value = RandomWhole(1, 10)
    y.value = RandomWhole(1, 10)


rolls = captured(volatile)
assert depends(rolls, 1, 0), rolls
assert Resource.VOLATILE in effects_of(rolls[0]).writes


# Nothing crosses a pause, in either direction.
def paused() -> None:
    x.value += 1
    pause_execution(1)
    y.value += 1


pause_program = captured(paused)
assert effects_of(pause_program[1]).control
assert depends(pause_program, 1, 0), pause_program
assert depends(pause_program, 2, 1), pause_program


# Unrelated stat writes have no edge between them at all.
def independent() -> None:
    x.value += 1
    y.value += 1


loose = captured(independent)
assert not depends(loose, 1, 0), loose


# `=` only writes its target; every other operator reads it first.
def assignment_shapes() -> None:
    x.value = 5
    x.value += 5


shapes = captured(assignment_shapes)
assert Resource.POSITION not in effects_of(shapes[0]).reads
assert x.into_hashable() in effects_of(shapes[0]).writes
assert x.into_hashable() not in effects_of(shapes[0]).reads
assert x.into_hashable() in effects_of(shapes[1]).reads


# A conditional carries the effects of its whole body, so what happens inside it
# still orders it against the rest of the block.
def guarded() -> None:
    with IfAll(x > 1):
        y.value += 1
    y.value += 2


conditional_program = captured(guarded)
assert y.into_hashable() in effects_of(conditional_program[0]).writes
assert depends(conditional_program, 1, 0), conditional_program


# Two actions that touch the same world resource stay ordered; different ones
# do not.
inventory = captured(lambda: (give_item(Item('stone')), full_heal()))
assert not depends(inventory, 1, 0), inventory
assert Resource.INVENTORY in effects_of(inventory[0]).writes
assert Resource.HEALTH in effects_of(inventory[1]).writes
