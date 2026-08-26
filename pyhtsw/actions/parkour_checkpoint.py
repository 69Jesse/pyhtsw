from typing import final

from pyhtsw.expression.expression import Expression
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

__all__ = (
    'ParkourCheckpointExpression',
    'parkour_checkpoint',
)


@final
class ParkourCheckpointExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='PARKOUR_CHECKPOINT',
        limit=1,
        effects=Effects.of(reads=(Resource.POSITION,), writes=(Resource.PARKOUR,)),
        display_name='Parkour Checkpoint',
        forbidden_events=('Player Quit',),
    )

    def into_htsl(self) -> str:
        return 'parkCheck'


def parkour_checkpoint() -> None:
    ParkourCheckpointExpression().write()
