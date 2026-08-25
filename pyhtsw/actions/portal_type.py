from typing import final

from ..expression.condition.condition import Condition
from ..types import PORTAL_TYPES

__all__ = ('PortalType',)


@final
class PortalType(Condition):
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

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, PortalType):
            return False
        return self.portal == other.portal

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.portal} inverted={self.inverted}>'
