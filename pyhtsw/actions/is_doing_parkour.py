from pyhtsw.registry import ConditionMeta
from pyhtsw.schedule import Resource

from ..expression.condition.named_condition import NamedCondition

__all__ = (
    'IsDoingParkourCondition',
    'IsDoingParkour',
)


class IsDoingParkourCondition(NamedCondition):
    htsw_meta = ConditionMeta(
        htsw_name='IS_DOING_PARKOUR',
        limit=1,
        reads=frozenset((Resource.PARKOUR,)),
    )

    def __init__(self) -> None:
        super().__init__('doingParkour')


IsDoingParkour = IsDoingParkourCondition()
