from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ClassVar, overload

from pyhtsw.utils.caller import caller_module

if TYPE_CHECKING:
    from pyhtsw.compiler.importable import Importable


__all__ = (
    'Declared',
    'declared_field',
    'declared_name',
    'register_importable',
)


def register_importable[ImportableT: 'Importable'](
    importable: ImportableT,
) -> ImportableT:
    """Attribute an importable to the user module that asked for it and put it
    in the current container. `caller_module` skips every pyhtsw frame, so this
    lands on the same module however many pyhtsw helpers deep the call is."""
    from pyhtsw.compiler.container import get_current_container

    importable.module = caller_module()
    get_current_container().register_importable(importable)
    return importable


@overload
def declared_name(value: 'Declared | str') -> str: ...


@overload
def declared_name(value: None) -> None: ...


def declared_name(value: 'Declared | str | None') -> str | None:
    """The identifier behind a reference: the class declares, the string
    refers, and either names the same importable."""
    if value is None or isinstance(value, str):
        return value
    return value.name


class declared_field[T]:
    """One field of the importable, reached through the value that declares it.
    Reading resolves the declaration; writing goes straight to the importable,
    so a value built by a factory can still be adjusted before export."""

    field: str

    def __init__(
        self,
        field: str | None = None,
        *,
        transform: Callable[[Any], T] | None = None,
        readonly: bool = False,
    ) -> None:
        if field is not None:
            self.field = field
        self.transform = transform
        self.readonly = readonly

    def __set_name__(self, owner: type, name: str) -> None:
        if not hasattr(self, 'field'):
            self.field = name

    @overload
    def __get__(self, obj: None, cls: type | None = None) -> 'declared_field[T]': ...

    @overload
    def __get__(self, obj: 'Declared', cls: type | None = None) -> T: ...

    def __get__(
        self,
        obj: 'Declared | None',
        cls: type | None = None,
    ) -> 'T | declared_field[T]':
        if obj is None:
            return self
        value = getattr(obj.declaration(self.field), self.field)
        return value if self.transform is None else self.transform(value)

    def __set__(self, obj: 'Declared', value: T) -> None:
        if self.readonly:
            raise AttributeError(
                f'"{self.field}" is read-only; it is a view of the declaration.',
            )
        setattr(obj.declaration(self.field), self.field, value)


class Declared:
    """A value that names an importable and reads its declared fields off it.

    Equality is by (kind, name), so two values naming the same declaration
    compare equal and resolve the same importable."""

    __htsw_kind__: ClassVar[str]
    __htsw_factory__: ClassVar[str]
    # None for a bare reference to something declared elsewhere (or in-game).
    __htsw_importable__: 'Importable | None' = None
    _name: str

    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        importable = self.__htsw_importable__
        return importable.identifier() if importable is not None else self._name

    @name.setter
    def name(self, value: str) -> None:
        importable = self.__htsw_importable__
        if importable is not None and value != importable.identifier():
            from pyhtsw.compiler.container import get_current_container

            get_current_container().rename_importable(importable, value)
        self._name = value

    @property
    def importable(self) -> 'Importable':
        """The declaration this value names. Raises when there is none."""
        return self.declaration()

    def declaration(self, field: str = 'declaration') -> 'Importable':
        declared = self.__htsw_importable__
        if declared is not None:
            return declared

        from pyhtsw.compiler.container import get_current_container

        kind = self.__htsw_kind__
        found = get_current_container().find_importable(kind, self._name)
        if found is None:
            label = type(self).__name__
            raise RuntimeError(
                f'{label} "{self._name}" was never declared, so it has no '
                f'{field} to read. Declare it with '
                f'{self.__htsw_factory__}("{self._name}", ...), or drop the '
                f'read - a plain {label}("{self._name}") only names one.',
            )
        return found

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Declared):
            return NotImplemented
        if other.__htsw_kind__ != self.__htsw_kind__:
            return NotImplemented
        return other.name == self.name

    def __hash__(self) -> int:
        return hash((self.__htsw_kind__, self.name))

    def __repr__(self) -> str:
        return f'{type(self).__name__}<{self.name}>'
