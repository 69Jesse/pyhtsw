from pyhtsw.expression.condition.named_condition import NamedCondition
from pyhtsw.registry import ConditionMeta

__all__ = (
    'CanPVPCondition',
    'CanPVP',
)


class CanPVPCondition(NamedCondition):
    htsw_meta = ConditionMeta(
        htsw_name='PVP_ENABLED',
        limit=20,
        reads=frozenset(()),
        display_name='Can PvP',
        scoped_events=('PvP State Change',),
    )

    def __init__(self) -> None:
        super().__init__('canPvp')


CanPVP = CanPVPCondition()
