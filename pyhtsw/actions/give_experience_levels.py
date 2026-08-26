from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.expression.expression import Expression
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

__all__ = (
    'GiveExperienceLevelsExpression',
    'give_experience_levels',
)


@final
class GiveExperienceLevelsExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='GIVE_EXPERIENCE_LEVELS',
        limit=5,
        effects=Effects.of(writes=(Resource.EXPERIENCE,)),
        display_name='Give Experience Levels',
        forbidden_events=('Player Quit',),
    )

    levels: int

    def __init__(self, levels: int) -> None:
        self.levels = levels

    def into_htsl(self) -> str:
        return f'xpLevel {self.inline(self.levels)}'

    def cloned(
        self,
        *,
        levels: int | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'levels': levels,
            },
        )


def give_experience_levels(levels: int) -> None:
    GiveExperienceLevelsExpression(levels=levels).write()
