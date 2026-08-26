from pyhtsw.expression.condition.named_condition import NamedCondition
from pyhtsw.registry import ConditionMeta

__all__ = (
    'PlayerSneakingCondition',
    'PlayerSneaking',
)


class PlayerSneakingCondition(NamedCondition):
    htsw_meta = ConditionMeta(
        htsw_name='IS_SNEAKING',
        reads=frozenset(()),
    )

    def __init__(self) -> None:
        super().__init__('isSneaking')


PlayerSneaking = PlayerSneakingCondition()
