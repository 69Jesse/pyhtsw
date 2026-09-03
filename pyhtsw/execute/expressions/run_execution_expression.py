from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Self

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.execute.expressions.execution_expression import ExecutionExpression
from pyhtsw.utils.callback import call_with_optional_arg

if TYPE_CHECKING:
    from pyhtsw.execute.house import EmulatedHouse


__all__ = (
    'CallbackType',
    'RunExecutionExpression',
)


type CallbackType = Callable[[], Any] | Callable[['EmulatedHouse'], Any]


class RunExecutionExpression(ExecutionExpression):
    callback: CallbackType

    def __init__(self, callback: CallbackType) -> None:
        self.callback = callback

    def raw_execute(self, context: 'EmulatedHouse') -> None:
        call_with_optional_arg(self.callback, context, noun='callback')

    def cloned(
        self,
        *,
        callback: CallbackType | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'callback': callback,
            },
        )
