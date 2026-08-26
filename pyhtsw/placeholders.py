from abc import ABC, abstractmethod
from typing import ClassVar, final

from pyhtsw.checkable import Checkable
from pyhtsw.editable import Editable
from pyhtsw.execute.backend_type import BackendType
from pyhtsw.internal_type import InternalType
from pyhtsw.registry import ActionMeta

__all__ = (
    'PlaceholderCheckable',
    'PlaceholderEditable',
)


class PlaceholderCheckable(Checkable, ABC):
    htsw_meta: ClassVar[ActionMeta] = ActionMeta()

    placeholder: str
    constant_internal_type: InternalType
    default_backend_value: BackendType

    def __init__(
        self,
        *,
        placeholder: str,
        constant_internal_type: InternalType,
    ) -> None:
        super().__init__(internal_type=constant_internal_type)
        self.placeholder = placeholder
        self.constant_internal_type = constant_internal_type

    @abstractmethod
    def get_backend_value(self) -> BackendType:
        raise NotImplementedError

    def is_execution_player_scoped(self) -> bool:
        # `%player.…%` placeholders resolve against the executing player; the
        # rest (`%server.…%`, `%house.…%`, …) are shared by everyone.
        return self.placeholder.startswith('%player.')

    @final
    def get_backend_fallback_value(self) -> BackendType | None:
        return super().get_backend_fallback_value() or self.get_backend_value()

    def into_string_lhs(self) -> str:
        return f'placeholder {self.inline_quoted(self.placeholder)}'

    def condition_takes_fallback(self) -> bool:
        return False

    def into_string_rhs(self, *, include_internal_type: bool = True) -> str:
        return self.format_with_internal_type(
            self.placeholder,
            include_internal_type=include_internal_type,
        )

    def into_inside_string(self, include_fallback_value: bool = True) -> str:
        return self.placeholder

    def equals_raw(self, other: object) -> bool:
        return self is other

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.placeholder}>'


class PlaceholderEditable(PlaceholderCheckable, Editable, ABC):
    assignment_lhs: str
    condition_lhs: str

    def __init__(
        self,
        *,
        assignment_lhs: str,
        placeholder: str,
        constant_internal_type: InternalType,
        condition_lhs: str | None = None,
    ) -> None:
        super().__init__(
            placeholder=placeholder,
            constant_internal_type=constant_internal_type,
        )
        self.assignment_lhs = assignment_lhs
        self.condition_lhs = condition_lhs or assignment_lhs

    def into_string_lhs(self) -> str:
        return self.assignment_lhs

    def into_condition_lhs(self) -> str:
        return self.condition_lhs
