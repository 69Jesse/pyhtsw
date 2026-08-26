from typing import final

from ..expression.expression import Expression

__all__ = (
    'FullHealExpression',
    'full_heal',
)


@final
class FullHealExpression(Expression):
    def into_htsl(self) -> str:
        return 'fullHeal'


def full_heal() -> None:
    FullHealExpression().write()
