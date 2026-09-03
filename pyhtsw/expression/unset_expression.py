from typing import TYPE_CHECKING, Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.compiler.registry import ActionMeta
from pyhtsw.expression.expression import Expression

if TYPE_CHECKING:
    from pyhtsw.execute.context import ExecutionContext
    from pyhtsw.stats.stat import Stat


@final
class UnsetExpression(Expression):
    # htsw counts `var "x" unset` as a Change Variable, sharing one budget with
    # `BinaryExpression`. `effects_of` special-cases this class before it reads
    # the meta, so declaring one does not change scheduling.
    htsw_meta = ActionMeta(
        htsw_name='CHANGE_VAR',
        limit=25,
    )

    target: 'Stat'

    def __init__(self, target: 'Stat') -> None:
        self.target = target

    def into_htsl(self) -> str:
        return f'{self.target.into_string_lhs()} unset'

    def raw_execute(self, context: 'ExecutionContext') -> None:
        context.pop(self.target)

    def cloned(
        self,
        *,
        target: 'Stat | Missing' = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'target': target,
            },
        )
