from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.expression.expression import Expression
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource, Stream

__all__ = (
    'FailParkourExpression',
    'fail_parkour',
)


@final
class FailParkourExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='FAIL_PARKOUR',
        limit=1,
        effects=Effects.of(
            writes=(
                Resource.PARKOUR,
                Resource.POSITION,
            ),
            stream=Stream.TEXT,
        ),
        display_name='Fail Parkour',
        forbidden_events=('Player Quit',),
    )

    reason: str

    def __init__(self, reason: str = 'Failed!') -> None:
        self.reason = reason

    def into_htsl(self) -> str:
        return f'failParkour {self.inline_quoted(self.reason)}'

    def cloned(
        self,
        *,
        reason: str | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'reason': reason,
            },
        )


def fail_parkour(reason: str = 'Failed!') -> None:
    FailParkourExpression(reason=reason).write()
