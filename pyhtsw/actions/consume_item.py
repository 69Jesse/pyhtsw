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

    def equals(self, other: object) -> bool:
        return isinstance(other, ConsumeItemExpression)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}'


def consume_item() -> None:
    ConsumeItemExpression().write()
