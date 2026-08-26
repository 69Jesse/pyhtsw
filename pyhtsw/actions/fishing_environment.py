from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.expression.condition.condition import Condition
from pyhtsw.registry import ConditionMeta
from pyhtsw.types import FISHING_ENVIRONMENTS

__all__ = ('FishingEnvironment',)


@final
class FishingEnvironment(Condition):
    htsw_meta = ConditionMeta(
        htsw_name='FISHING_ENVIRONMENT',
        limit=20,
        reads=frozenset(()),
        display_name='Fishing Environment',
        scoped_events=('Fish Caught',),
    )

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
