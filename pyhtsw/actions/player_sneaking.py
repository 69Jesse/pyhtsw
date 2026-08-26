from pyhtsw.registry import ConditionMeta

from ..expression.condition.named_condition import NamedCondition

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
