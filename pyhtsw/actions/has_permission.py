from typing import final

from ..expression.condition.condition import Condition
from ..types import ALL_PERMISSIONS

__all__ = ('HasPermission',)


@final
class HasPermission(Condition):
    permission: ALL_PERMISSIONS

    def __init__(
        self,
        permission: ALL_PERMISSIONS,
    ) -> None:
        self.permission = permission

    def into_htsl_raw(self) -> str:
        return f'hasPermission {self.inline_quoted(self.permission)}'

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, HasPermission):
            return False
        return self.permission == other.permission

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.permission} inverted={self.inverted}>'
