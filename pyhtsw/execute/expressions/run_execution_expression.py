from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Self

from pyhtsw.clone import MISSING, Missing, clone_with

from ...utils.callback import call_with_optional_arg
from .execution_expression import ExecutionExpression

if TYPE_CHECKING:
    from ..context import ExecutionContext


__all__ = (
    'CallbackType',
    'RunExecutionExpression',
)


type CallbackType = Callable[[], Any] | Callable[['ExecutionContext'], Any]


class RunExecutionExpression(ExecutionExpression):
    callback: CallbackType

    def __init__(self, callback: CallbackType) -> None:
        self.callback = callback

    def raw_execute(self, context: 'ExecutionContext') -> None:
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
