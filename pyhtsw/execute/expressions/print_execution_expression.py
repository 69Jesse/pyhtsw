from collections.abc import Callable
from typing import TYPE_CHECKING, Self

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.execute.expressions.execution_expression import ExecutionExpression
from pyhtsw.utils.callback import call_with_optional_args
from pyhtsw.utils.log import log

if TYPE_CHECKING:
    from pyhtsw.execute.house import EmulatedHouse


__all__ = ('PrintExecutionExpression',)


class PrintExecutionExpression(ExecutionExpression):
    values: tuple[
        object | Callable[[], object] | Callable[['EmulatedHouse'], object],
        ...,
    ]
    cast: bool

    def __init__(
        self,
        values: tuple[
            object | Callable[[], object] | Callable[['EmulatedHouse'], object],
            ...,
        ],
        *,
        cast: bool = False,
    ) -> None:
        self.values = values
        self.cast = cast

    def flattened_values(self, context: 'EmulatedHouse') -> tuple[object, ...]:
        flattened = []
        for value in self.values:
            if callable(value):
                flattened.append(call_with_optional_args(value, context, noun='values'))
            else:
                flattened.append(value)
        return tuple(flattened)

    def raw_execute(self, context: 'EmulatedHouse') -> None:
        line = ' '.join(map(str, self.flattened_values(context)))
        log(context.get(line, cast=self.cast, output='string'))

    def cloned(
        self,
        *,
        values: tuple[
            object | Callable[[], object] | Callable[['EmulatedHouse'], object],
            ...,
        ]
        | Missing = MISSING,
        cast: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'values': values,
                'cast': cast,
            },
        )
