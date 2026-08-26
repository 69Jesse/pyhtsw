from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource

from ..checkable import Checkable
from ..expression.expression import Expression
from ..expression.housing_type import NumericHousingType

__all__ = (
    'ChangeVelocityExpression',
    'change_velocity',
)


@final
class ChangeVelocityExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='SET_VELOCITY',
        limit=5,
        effects=Effects.of(writes=(Resource.VELOCITY,)),
        display_name='Change Velocity',
        forbidden_events=('Player Quit',),
    )

    x: Checkable | NumericHousingType
    y: Checkable | NumericHousingType
    z: Checkable | NumericHousingType

    def __init__(
        self,
        x: Checkable | NumericHousingType,
        y: Checkable | NumericHousingType,
        z: Checkable | NumericHousingType,
    ) -> None:
        self.x = x
        self.y = y
        self.z = z

    def into_htsl(self) -> str:
        return f'changeVelocity {self.inline(self.x)} {self.inline(self.y)} {self.inline(self.z)}'

    def cloned(
        self,
        *,
        x: Checkable | NumericHousingType | Missing = MISSING,
        y: Checkable | NumericHousingType | Missing = MISSING,
        z: Checkable | NumericHousingType | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'x': x,
                'y': y,
                'z': z,
            },
        )


def change_velocity(
    x: Checkable | NumericHousingType,
    y: Checkable | NumericHousingType,
    z: Checkable | NumericHousingType,
) -> None:
    ChangeVelocityExpression(x=x, y=y, z=z).write()
