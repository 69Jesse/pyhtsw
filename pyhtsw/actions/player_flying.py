from pyhtsw.registry import ConditionMeta
from pyhtsw.schedule import Resource

from ..expression.condition.named_condition import NamedCondition

__all__ = (
    'PlayerFlyingCondition',
    'PlayerFlying',
)


class PlayerFlyingCondition(NamedCondition):
    htsw_meta = ConditionMeta(
        htsw_name='IS_FLYING',
        reads=frozenset((Resource.GAMEMODE,)),
    )

    def __init__(self) -> None:
        super().__init__('isFlying')


PlayerFlying = PlayerFlyingCondition()
