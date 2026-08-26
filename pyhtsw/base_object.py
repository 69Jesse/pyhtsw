from abc import ABC
from typing import TYPE_CHECKING, Any, ClassVar, Self, final

from .clone import build_clone_spec, clone_with
from .expression.housing_type import housing_type_as_rhs

if TYPE_CHECKING:
    from .checkable import Checkable
    from .expression.housing_type import HousingType


class BaseObject(ABC):  # noqa: B024
    # Derived from `__init__` at class creation; see the Cloning section in
    # CLAUDE.md for why the constructor is the single source of truth.
    __clone_fields__: ClassVar[tuple[str, ...]] = ()
    __clone_posonly__: ClassVar[int] = 0
    __clone_map__: ClassVar[dict[str, str]] = {}
    __clone_extra__: ClassVar[tuple[str, ...]] = ()
    __clone_carry__: ClassVar[tuple[str, ...]] = ()
    __clone_compare__: ClassVar[tuple[str, ...]] = ()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        build_clone_spec(cls)

    def cloned(self, *args: Any, **overrides: Any) -> Self:
        """Returns a copy, overriding only the given fields."""
        if args:
            raise TypeError(
                f'{type(self).__name__}.cloned() takes no positional arguments',
            )
        if overrides:
            unknown = set(overrides).difference(
                self.__clone_fields__,
                self.__clone_carry__,
            )
            if unknown:
                raise TypeError(
                    f'{type(self).__name__}.cloned() got unexpected field(s): '
                    f'{", ".join(sorted(unknown))}',
                )
        return clone_with(self, overrides)

    @staticmethod
    def cloned_or_same[T: object](value: T) -> T:
        if isinstance(value, BaseObject):
            return value.cloned()
        return value

    def equals(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.fields_equal(other)

    @final
    def fields_equal(self, other: 'BaseObject') -> bool:
        return all(
            self.equals_or_eq(getattr(self, name), getattr(other, name))
            for name in self.__clone_compare__
        )

    @staticmethod
    def equals_or_eq(a: object, b: object) -> bool:
        if isinstance(a, BaseObject) and isinstance(b, BaseObject):
            return a.equals(b)
        if (
            isinstance(a, list | tuple)
            and isinstance(b, list | tuple)
            and type(a) is type(b)
            and len(a) == len(b)
        ):
            return all(BaseObject.equals_or_eq(x, y) for x, y in zip(a, b, strict=True))
        if not isinstance(a, BaseObject) and not isinstance(b, BaseObject):
            return a == b
        return False

    def __repr__(self) -> str:
        inner = ', '.join(
            f'{name}={getattr(self, name)!r}' for name in self.__clone_compare__
        )
        return f'{type(self).__name__}<{inner}>'

    @staticmethod
    def inline(value: 'Checkable | HousingType | bool') -> str:
        from .checkable import Checkable

        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, Checkable):
            return str(value)
        return housing_type_as_rhs(value)

    @staticmethod
    def inline_quoted(value: 'Checkable | str') -> str:
        return f'"{str(value).replace('"', '\\"')}"'
