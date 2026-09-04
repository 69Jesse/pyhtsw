from collections.abc import Callable
from typing import Unpack

from pyhtsw.compiler.settings import ContainerSettings
from pyhtsw.execute.expressions.run_execution_expression import CallbackType
from pyhtsw.execute.house import EmulatedHouse
from pyhtsw.expression.expression import Expression
from pyhtsw.utils.callback import call_with_optional_args

__all__ = (
    'emulate',
    'run_saved_emulations',
)


_saved_emulations: list[tuple[EmulatedHouse, CallbackType]] = []


def emulate(
    *,
    verbose: bool = False,
    expression_callback: Callable[[Expression], None] | None = None,
    pause_multiplier: float = 1.0,
    volume_multiplier: float = 0.1,
    **settings: Unpack[ContainerSettings],
) -> Callable[[CallbackType], EmulatedHouse]:
    def decorator(callback: CallbackType) -> EmulatedHouse:
        house = EmulatedHouse(
            verbose=verbose,
            expression_callback=expression_callback,
            pause_multiplier=pause_multiplier,
            volume_multiplier=volume_multiplier,
            **settings,
        )
        _saved_emulations.append((house, callback))
        return house

    return decorator


def run_saved_emulations() -> None:
    while _saved_emulations:
        house, callback = _saved_emulations.pop(0)
        with house:
            call_with_optional_args(callback, house, noun='callback')
