from pyhtsw.directives.base import Directive

__all__ = (
    'OPTIMIZATION_PASSES',
    'NoOptimization',
    'optimization_enabled',
)


# Every individually switchable pass. `temp_merge` collapses `tmp = x; y = tmp`;
# `no_ops` drops `+= 0` and friends; `fold` folds adjacent constant ops;
# `identity_merge` collapses `x = 0; x += y`; `dead_stores` drops overwritten
# writes; `reorder` schedules expressions; `merge_conditionals` joins
# conditionals that check the same thing; `dead_code` drops what cannot run.
OPTIMIZATION_PASSES = (
    'temp_merge',
    'no_ops',
    'fold',
    'identity_merge',
    'dead_stores',
    'reorder',
    'merge_conditionals',
    'dead_code',
)


class NoOptimization(Directive):
    """Disables optimization passes for the duration of the block.

    A bare `NoOptimization()` disables every pass. Naming a pass keeps it
    running, so everything is off by default and you opt back in:

        with NoOptimization(fold=True):
            ...  # only the constant folder still runs

    Nested blocks intersect: a pass runs only if every open block allows it.
    """

    enabled: frozenset[str]

    def __init__(self, **passes: bool) -> None:
        unknown = sorted(set(passes) - set(OPTIMIZATION_PASSES))
        if unknown:
            raise TypeError(
                f'Unknown optimization pass(es): {", ".join(unknown)}. '
                f'Valid passes: {", ".join(OPTIMIZATION_PASSES)}',
            )
        self.enabled = frozenset(name for name, keep in passes.items() if keep)


def optimization_enabled(pass_name: str) -> bool:
    return all(pass_name in frame.enabled for frame in NoOptimization._stack)


def no_optimization() -> bool:
    """True when no pass at all may run."""
    return NoOptimization.active() and not any(
        optimization_enabled(pass_name) for pass_name in OPTIMIZATION_PASSES
    )
