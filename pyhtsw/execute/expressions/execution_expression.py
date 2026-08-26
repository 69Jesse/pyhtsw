from pyhtsw.compiler.registry import ActionMeta
from pyhtsw.expression.expression import Expression

__all__ = ('ExecutionExpression',)


class ExecutionExpression(Expression):
    htsw_meta = ActionMeta(
        control=True,
    )

    def into_htsl(self) -> str:
        return f'// @ignore {self!r}'
