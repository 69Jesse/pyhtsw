from pyhtsw.expression.condition.named_condition import NamedCondition
from pyhtsw.registry import ConditionMeta
from pyhtsw.schedule import Resource

__all__ = (
    'IsFlyingCondition',
    'IsFlying',
)


class IsFlyingCondition(NamedCondition):
    htsw_meta = ConditionMeta(
        htsw_name='IS_FLYING',
        limit=20,
        reads=frozenset((Resource.GAMEMODE,)),
    )

    def __init__(self) -> None:
        super().__init__('isFlying')


IsFlying = IsFlyingCondition()
