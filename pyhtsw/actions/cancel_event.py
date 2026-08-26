from typing import final

from pyhtsw.expression.expression import Expression
from pyhtsw.registry import ActionMeta

__all__ = (
    'CancelEventExpression',
    'cancel_event',
)


@final
class CancelEventExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='CANCEL_EVENT',
        limit=1,
        control=True,
        display_name='Cancel Event',
    )

    def into_htsl(self) -> str:
        return 'cancelEvent'


def cancel_event() -> None:
    CancelEventExpression().write()
