from typing import TYPE_CHECKING, final

from ..expression.expression import Expression

if TYPE_CHECKING:
    from ..execute.context import ExecutionContext


__all__ = (
    'ExitFunctionExpression',
    'exit_function',
)


@final
class ExitFunctionExpression(Expression):
    def into_htsl(self) -> str:
        return 'exit'

    def raw_execute(self, context: 'ExecutionContext') -> None:
        from ..execute.signal import ExitSignal

        raise ExitSignal()


def exit_function() -> None:
    ExitFunctionExpression().write()
