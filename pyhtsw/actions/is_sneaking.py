from pyhtsw.registry import ConditionMeta

from ..expression.condition.named_condition import NamedCondition

__all__ = (
    'IsSneakingCondition',
    'IsSneaking',
)


class IsSneakingCondition(NamedCondition):
    htsw_meta = ConditionMeta(
        htsw_name='IS_SNEAKING',
        limit=20,
        reads=frozenset(()),
    )

    def __init__(self) -> None:
        super().__init__('isSneaking')


IsSneaking = IsSneakingCondition()
