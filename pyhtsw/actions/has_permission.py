from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with

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

    def cloned(
        self,
        *,
        permission: ALL_PERMISSIONS | Missing = MISSING,
        inverted: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'permission': permission,
                'inverted': inverted,
            },
        )
