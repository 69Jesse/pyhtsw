from typing import final

from ..expression.expression import Expression

__all__ = (
    'GoToHouseSpawnExpression',
    'go_to_house_spawn',
)


@final
class GoToHouseSpawnExpression(Expression):
    def into_htsl(self) -> str:
        return 'houseSpawn'

    def equals(self, other: object) -> bool:
        return isinstance(other, GoToHouseSpawnExpression)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}'


def go_to_house_spawn() -> None:
    GoToHouseSpawnExpression().write()
