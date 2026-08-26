from typing import TYPE_CHECKING, final

from pyhtsw.expression.expression import Expression
from pyhtsw.registry import ActionMeta

if TYPE_CHECKING:
    from pyhtsw.execute.context import ExecutionContext


__all__ = (
    'ExitFunctionExpression',
    'exit_function',
)


@final
class ExitFunctionExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='EXIT',
        limit=1,
        control=True,
        display_name='Exit',
    )

    def into_htsl(self) -> str:
        return 'exit'

    def raw_execute(self, context: 'ExecutionContext') -> None:
        from pyhtsw.execute.signal import ExitSignal

        raise ExitSignal()


def exit_function() -> None:
    ExitFunctionExpression().write()
