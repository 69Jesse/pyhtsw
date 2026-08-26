from typing import TYPE_CHECKING, Self, final

from pyhtsw.clone import MISSING, Missing, clone_with

from ..expression.expression import Expression
from .function import Function

if TYPE_CHECKING:
    from ..execute.context import ExecutionContext


__all__ = (
    'TriggerFunctionExpression',
    'trigger_function',
)


@final
class TriggerFunctionExpression(Expression):
    function: Function
    trigger_for_all_players: bool

    def __init__(
        self,
        function: Function,
        trigger_for_all_players: bool = False,
    ) -> None:
        self.function = function
        self.trigger_for_all_players = trigger_for_all_players

    def into_htsl(self) -> str:
        return f'function {self.inline_quoted(self.function.name)} {self.inline(self.trigger_for_all_players)}'

    def referenced_importables(self) -> list[tuple[str, str]]:
        return [('functions', self.function.name)]

    def raw_execute(self, context: 'ExecutionContext') -> None:
        context.execute_function(
            self.function,
            all_players=self.trigger_for_all_players,
        )

    def cloned(
        self,
        *,
        function: Function | Missing = MISSING,
        trigger_for_all_players: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'function': function,
                'trigger_for_all_players': trigger_for_all_players,
            },
        )


def trigger_function(
    function: Function | str,
    trigger_for_all_players: bool = False,
) -> None:
    function = function if isinstance(function, Function) else Function(function)
    TriggerFunctionExpression(
        function=function,
        trigger_for_all_players=trigger_for_all_players,
    ).write()
