from typing import final

from ..expression.expression import Expression

__all__ = (
    'ParkourCheckpointExpression',
    'parkour_checkpoint',
)


@final
class ParkourCheckpointExpression(Expression):
    def into_htsl(self) -> str:
        return 'parkCheck'


def parkour_checkpoint() -> None:
    ParkourCheckpointExpression().write()
