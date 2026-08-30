from collections.abc import Callable
from typing import Unpack

from pyhtsw.compiler.settings import ContainerSettings
from pyhtsw.execute.context import ExecutionContext
from pyhtsw.execute.expressions.run_execution_expression import CallbackType
from pyhtsw.expression.expression import Expression
from pyhtsw.utils.callback import call_with_optional_arg

__all__ = (
    'execute',
    'run_saved_execution_contexts',
)


_saved_execution_contexts: list[tuple[ExecutionContext, CallbackType]] = []


def execute(
    *,
    verbose: bool = False,
    expression_callback: Callable[[Expression], None] | None = None,
    pause_multiplier: float = 1.0,
    volume_multiplier: float = 0.1,
    **settings: Unpack[ContainerSettings],
) -> Callable[[CallbackType], ExecutionContext]:
    def decorator(callback: CallbackType) -> ExecutionContext:
        context = ExecutionContext(
            verbose=verbose,
            expression_callback=expression_callback,
            pause_multiplier=pause_multiplier,
            volume_multiplier=volume_multiplier,
            **settings,
        )
        _saved_execution_contexts.append((context, callback))
        return context

    return decorator


def run_saved_execution_contexts() -> None:
    while _saved_execution_contexts:
        context, callback = _saved_execution_contexts.pop(0)
        with context:
            call_with_optional_arg(callback, context, noun='callback')
