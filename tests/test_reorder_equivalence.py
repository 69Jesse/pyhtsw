import io
import random
import re
from contextlib import redirect_stdout

from pyhtsw import (
    Container,
    ExecutionContext,
    IfAll,
    NoOptimization,
    PlayerStat,
    chat,
    create_function,
    full_heal,
    give_experience_levels,
    pause_execution,
    play_sound,
)
from pyhtsw.directives.no_optimization import OPTIMIZATION_PASSES

ONLY_REORDER_OFF = {name: True for name in OPTIMIZATION_PASSES if name != 'reorder'}

SEEDS = range(60)
STAT_NAMES = ('p', 'q', 'r', 's')
STATS = {name: PlayerStat(name).as_long() for name in STAT_NAMES}


def emit(rng: random.Random, *, allow_barriers: bool) -> None:
    """Write one random program into the current container."""
    kinds = ['set', 'add', 'mul', 'copy', 'chat', 'cond', 'heal', 'xp']
    if allow_barriers:
        kinds += ['pause', 'sound']
    for _ in range(rng.randint(6, 22)):
        kind = rng.choice(kinds)
        target = STATS[rng.choice(STAT_NAMES)]
        other = STATS[rng.choice(STAT_NAMES)]
        if kind == 'set':
            target.value = rng.randint(-5, 20)
        elif kind == 'add':
            target.value += rng.randint(-5, 20)
        elif kind == 'mul':
            target.value *= rng.randint(1, 4)
        elif kind == 'copy':
            target.value = other
        elif kind == 'chat':
            chat(f'v={target} w={other}')
        elif kind == 'cond':
            with IfAll(target > rng.randint(0, 10)):
                other.value += rng.randint(1, 5)
        elif kind == 'heal':
            full_heal()
        elif kind == 'xp':
            give_experience_levels(rng.randint(1, 3))
        elif kind == 'pause':
            pause_execution(1)
        elif kind == 'sound':
            play_sound('note.pling')


def executed(seed: int, *, reorder: bool) -> tuple[dict[str, object], list[str]]:
    """Final stat values plus the chat lines the run printed."""
    captured = io.StringIO()

    def run() -> ExecutionContext:
        with ExecutionContext() as context:
            for index, name in enumerate(STAT_NAMES):
                context.put(STATS[name], index + 1, ignore_warning=True)
            emit(random.Random(seed), allow_barriers=False)
        return context

    with redirect_stdout(captured):
        if reorder:
            context = run()
        else:
            with NoOptimization(**ONLY_REORDER_OFF):
                context = run()

    values: dict[str, object] = {
        name: context.get_raw(STATS[name]) for name in STAT_NAMES
    }
    lines = [
        line for line in captured.getvalue().split('\n') if line.strip().startswith('*')
    ]
    return values, lines


def _render(seed: int, flags: 'NoOptimization | None') -> str:
    def run() -> Container:
        with Container() as container:
            create_function('fuzz')(
                lambda: emit(random.Random(seed), allow_barriers=True),
            )
        return container

    if flags is None:
        container = run()
    else:
        with flags:
            container = run()
    return '\n'.join(
        block.into_htsl() for block in container.blocks if not block.is_empty()
    )


def rendered(seed: int, *, reorder: bool) -> str:
    """The full optimizer, with only the scheduler toggled."""
    return _render(seed, None if reorder else NoOptimization(**ONLY_REORDER_OFF))


def rendered_isolated(seed: int, *, reorder: bool) -> str:
    """Only the scheduler runs, so no pass can add or remove an action and the
    two renderings must be permutations of each other."""
    return _render(seed, NoOptimization(reorder=True) if reorder else NoOptimization())


def action_lines(htsl: str) -> list[str]:
    return [line.strip() for line in htsl.split('\n') if line.strip()]


def stream(htsl: str, prefix: str) -> list[str]:
    return [line for line in action_lines(htsl) if line.startswith(prefix)]


def around_pauses(htsl: str) -> list[frozenset[str]]:
    """The multiset of actions between each pair of consecutive pauses. Rendered
    as sorted tuples so a legal reshuffle inside one segment does not count."""
    segments: list[list[str]] = [[]]
    for line in action_lines(htsl):
        if re.fullmatch(r'pause \d+', line):
            segments.append([])
            continue
        if line in ('}', '{') or line.startswith(('if and', 'if or', '} else')):
            continue
        segments[-1].append(line)
    return [frozenset(sorted(segment)) for segment in segments]


for seed in SEEDS:
    plain_values, plain_chat = executed(seed, reorder=False)
    reordered_values, reordered_chat = executed(seed, reorder=True)
    assert plain_values == reordered_values, (seed, plain_values, reordered_values)
    assert plain_chat == reordered_chat, (seed, plain_chat, reordered_chat)

    # Chat and sound lines are never folded away, so the streams can be compared
    # with the whole optimizer running.
    plain_htsl = rendered(seed, reorder=False)
    reordered_htsl = rendered(seed, reorder=True)
    assert stream(plain_htsl, 'chat ') == stream(reordered_htsl, 'chat '), seed
    assert stream(plain_htsl, 'sound ') == stream(reordered_htsl, 'sound '), seed

    # With every other pass off, moving is the only thing that can happen: same
    # actions overall, and none of them across a pause.
    plain_only = rendered_isolated(seed, reorder=False)
    moved_only = rendered_isolated(seed, reorder=True)
    assert sorted(action_lines(plain_only)) == sorted(action_lines(moved_only)), seed
    assert around_pauses(plain_only) == around_pauses(moved_only), seed
