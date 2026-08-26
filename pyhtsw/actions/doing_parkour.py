from pyhtsw.expression.condition.named_condition import NamedCondition
from pyhtsw.registry import ConditionMeta
from pyhtsw.schedule import Resource

__all__ = (
    'DoingParkourCondition',
    'DoingParkour',
)


class DoingParkourCondition(NamedCondition):
    htsw_meta = ConditionMeta(
        htsw_name='IS_DOING_PARKOUR',
        limit=1,
        reads=frozenset((Resource.PARKOUR,)),
    )

    def __init__(self) -> None:
        super().__init__('doingParkour')


DoingParkour = DoingParkourCondition()
