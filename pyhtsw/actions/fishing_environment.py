from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with

from ..expression.condition.condition import Condition
from ..types import FISHING_ENVIRONMENTS

__all__ = ('FishingEnvironment',)


@final
class FishingEnvironment(Condition):
    environment: FISHING_ENVIRONMENTS

    def __init__(
        self,
        environment: FISHING_ENVIRONMENTS,
    ) -> None:
        self.environment = environment

    def into_htsl_raw(self) -> str:
        return f'fishingEnv {self.inline_quoted(self.environment)}'

    def cloned(
        self,
        *,
        environment: FISHING_ENVIRONMENTS | Missing = MISSING,
        inverted: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'environment': environment,
                'inverted': inverted,
            },
        )
