from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.expression.condition.condition import Condition
from pyhtsw.registry import ConditionMeta
from pyhtsw.types import PORTAL_TYPES

__all__ = ('PortalType',)


@final
class PortalType(Condition):
    htsw_meta = ConditionMeta(
        htsw_name='PORTAL_TYPE',
        limit=20,
        reads=frozenset(()),
        display_name='Portal Type',
        scoped_events=('Player Enter Portal',),
    )

    portal: PORTAL_TYPES

    def __init__(
        self,
        portal: PORTAL_TYPES,
    ) -> None:
        self.portal = portal

    def into_htsl_raw(self) -> str:
        # htsw's identifier form for this condition is unquoted and
        # underscore-joined: `portal Nether_Portal`.
        return f'portal {self.portal.replace(" ", "_")}'

    def cloned(
        self,
        *,
        portal: PORTAL_TYPES | Missing = MISSING,
        inverted: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'portal': portal,
                'inverted': inverted,
            },
        )
