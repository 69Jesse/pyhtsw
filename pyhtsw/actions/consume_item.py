from typing import final

from ..expression.expression import Expression

__all__ = (
    'ConsumeItemExpression',
    'consume_item',
)


@final
class ConsumeItemExpression(Expression):
    def into_htsl(self) -> str:
        return 'consumeItem'


def consume_item() -> None:
    ConsumeItemExpression().write()
