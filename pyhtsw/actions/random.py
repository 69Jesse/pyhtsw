import random
from collections.abc import Generator
from typing import TYPE_CHECKING, Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.config import INDENT
from pyhtsw.container import Container, ContainerContextManager, ExpressionContext
from pyhtsw.expression.expression import Expression
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

if TYPE_CHECKING:
    from pyhtsw.execute.context import ExecutionContext

__all__ = (
    'RandomContextManager',
    'RandomExpression',
    'Random',
)


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
