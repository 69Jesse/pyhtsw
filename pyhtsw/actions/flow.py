import random
from collections.abc import Generator
from typing import TYPE_CHECKING, Literal, Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.compiler.container import (
    Container,
    ContainerContextManager,
    ExpressionContext,
    get_current_container,
)
from pyhtsw.compiler.registry import ActionMeta
from pyhtsw.compiler.schedule import Effects, Resource
from pyhtsw.declarations.function import Function
from pyhtsw.expression.condition.condition import Condition
from pyhtsw.expression.condition.conditional_expression import (
    ConditionalExpression,
    ConditionalMode,
)
from pyhtsw.expression.expression import INDENT, Expression
from pyhtsw.utils.bounds import check_bounds

__all__ = (
    'ExitFunctionExpression',
    'exit_function',
    'PauseExecutionExpression',
    'pause_execution',
    'CancelEventExpression',
    'cancel_event',
    'TriggerFunctionExpression',
    'trigger_function',
    'RandomContextManager',
    'RandomExpression',
    'Random',
    'IfAll',
    'IfAny',
)

if TYPE_CHECKING:
    from pyhtsw.execute.context import ExecutionContext


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


if TYPE_CHECKING:
    from pyhtsw.execute.context import ExecutionContext


@final
class PauseExecutionExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='PAUSE',
        limit=30,
        control=True,
    )

    ticks: int

    def __init__(self, ticks: int = 20) -> None:
        self.ticks = check_bounds(
            ticks,
            field='pause_execution ticks',
            minimum=1,
            maximum=1000,
        )

    def into_htsl(self) -> str:
        return f'pause {self.inline(self.ticks)}'

    def raw_execute(self, context: 'ExecutionContext') -> None:
        from pyhtsw.execute.signal import PauseSignal

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


@final
class CancelEventExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='CANCEL_EVENT',
        limit=1,
        control=True,
        display_name='Cancel Event',
    )

    def into_htsl(self) -> str:
        return 'cancelEvent'


def cancel_event() -> None:
    CancelEventExpression().write()


if TYPE_CHECKING:
    from pyhtsw.execute.context import ExecutionContext


@final
class TriggerFunctionExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='FUNCTION',
        limit=10,
        control=True,
    )

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


if TYPE_CHECKING:
    from pyhtsw.execute.context import ExecutionContext


@final
class RandomExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='RANDOM',
        limit=25,
        effects=Effects.of(reads=(Resource.VOLATILE,), writes=(Resource.VOLATILE,)),
        display_name='Random Action',
    )

    expressions: list[Expression]

    def __init__(
        self,
        *,
        expressions: list[Expression] | None = None,
    ) -> None:
        self.expressions = expressions or []

    def into_htsl(self) -> str:
        result = 'random {'
        for expr in self.expressions:
            result += ('\n' + expr.into_htsl()).replace('\n', '\n' + INDENT)
        result += '\n}'
        return result

    def walk_expressions(self) -> Generator[Expression]:
        yield from super().walk_expressions()
        for expr in self.expressions:
            yield from expr.walk_expressions()

    def raw_execute(self, context: 'ExecutionContext') -> None:
        # A Random action runs exactly *one* of its actions, chosen uniformly —
        # it is a list of alternatives, not a block. With a single action inside
        # it is therefore deterministic, which is what makes it usable as a way
        # to spend an action outside the enclosing list's per-type budget.
        if not self.expressions:
            return
        chosen = self.expressions[random.randrange(len(self.expressions))]
        context.run_expressions([chosen])

    def finalize(self, container: Container) -> None:
        container.finalize_expressions(self.expressions)

    def nested_expressions_refs(self) -> list[list['Expression']]:
        return [self.expressions]

    def describe_nestable_block(self) -> str:
        return 'Random'

    def cloned(
        self,
        *,
        expressions: list[Expression] | None | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'expressions': expressions,
            },
        )


@final
class RandomContextManager(ContainerContextManager):
    expression: RandomExpression

    def __init__(self) -> None:
        self.expression = RandomExpression()

    def create_context(self) -> ExpressionContext:
        self.expression = RandomExpression()
        return ExpressionContext(
            parent_expression=self.expression,
            expressions_ref=self.expression.expressions,
        )


Random = RandomContextManager()


@final
class IfContextManager(ContainerContextManager):
    expression: ConditionalExpression

    def __init__(self, conditions: list['Condition'], mode: ConditionalMode) -> None:
        self.expression = ConditionalExpression(conditions, mode)

    def cloned(self) -> 'IfContextManager':
        return IfContextManager(
            [condition.cloned() for condition in self.expression.conditions],
            self.expression.mode,
        )

    def create_context(self) -> ExpressionContext:
        return ExpressionContext(
            parent_expression=self.expression,
            expressions_ref=self.expression.if_expressions,
        )


@final
class ElseContextManager(ContainerContextManager):
    def create_context(self) -> ExpressionContext:
        expressions = get_current_container().get_expressions_ref_in_context()
        if len(expressions) == 0 or not isinstance(
            expressions[-1],
            ConditionalExpression,
        ):
            raise SyntaxError('else without matching if')

        expression = expressions[-1]
        return ExpressionContext(
            parent_expression=expression,
            expressions_ref=expression.else_expressions,
            add_expression_to_container=False,
        )


def IfAll(*conditions: Condition | Literal[False]) -> IfContextManager:
    return IfContextManager(
        [c for c in conditions if c is not False],
        mode=ConditionalMode.ALL,
    )


def IfAny(
    *conditions: Condition | Literal[False],
    all_if_no_conditions: bool = True,
) -> IfContextManager:
    filtered = [c for c in conditions if c is not False]
    return IfContextManager(
        filtered,
        mode=ConditionalMode.ANY
        if len(filtered) > 1 or not all_if_no_conditions
        else ConditionalMode.ALL,
    )


Else: ElseContextManager = ElseContextManager()
