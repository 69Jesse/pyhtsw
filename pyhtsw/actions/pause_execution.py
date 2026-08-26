from typing import TYPE_CHECKING, Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.registry import ActionMeta

from ..expression.expression import Expression

if TYPE_CHECKING:
    from ..execute.context import ExecutionContext


__all__ = (
    'PauseExecutionExpression',
    'pause_execution',
)


@final
class PauseExecutionExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='PAUSE',
        limit=30,
        control=True,
    )

    ticks: int

    def __init__(self, ticks: int = 20) -> None:
        self.ticks = ticks

    def into_htsl(self) -> str:
        return f'pause {self.inline(self.ticks)}'

    def raw_execute(self, context: 'ExecutionContext') -> None:
        from ..execute.signal import PauseSignal

        raise PauseSignal(self.ticks)

    def cloned(
        self,
        *,
        ticks: int | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'ticks': ticks,
            },
        )


def pause_execution(ticks: int = 20) -> None:
    PauseExecutionExpression(ticks=ticks).write()
