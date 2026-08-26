from typing import final

from pyhtsw.expression.expression import Expression
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

__all__ = (
    'GoToHouseSpawnExpression',
    'go_to_house_spawn',
)


@final
class GoToHouseSpawnExpression(Expression):
    htsw_meta = ActionMeta(
        effects=Effects.of(writes=(Resource.POSITION,)),
    )

    def into_htsl(self) -> str:
        return 'houseSpawn'


def go_to_house_spawn() -> None:
    GoToHouseSpawnExpression().write()
