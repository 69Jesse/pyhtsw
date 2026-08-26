from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with

from ..expression.expression import Expression

__all__ = (
    'GiveExperienceLevelsExpression',
    'give_experience_levels',
)


@final
class GiveExperienceLevelsExpression(Expression):
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
