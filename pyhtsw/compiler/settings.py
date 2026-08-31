import re
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypedDict, overload

from pyhtsw.clone import MISSING

if TYPE_CHECKING:
    from pyhtsw.compiler.container import Container


__all__ = (
    'ContainerSettings',
    'SETTING_NAMES',
    'setting',
    'inherited_setting',
)


class ContainerSettings(TypedDict, total=False):
    """The keywords `Container(...)`, `container.configure(...)` and
    `pyhtsw.configure(...)` take. Each one is also a plain attribute."""

    project_name: str | None
    house_uuid: str | None
    projects_folder: 'Path | str | None'
    cleanup_stale_files: bool
    display_output: bool
    auto_export: bool
    ignore_action_limits: bool
    ignore_scope: bool
    allow_nested_expressions: bool


SETTING_NAMES: frozenset[str] = frozenset(ContainerSettings.__optional_keys__)


class setting[T]:
    """One field of a container's configuration, stored per container.

    Validation runs on assignment so a bad value's traceback lands on the line
    that set it rather than at export."""

    name: str

    def __init__(
        self,
        default: T,
        *,
        transform: Callable[[Any], T] | None = None,
    ) -> None:
        self.default = default
        self.transform = transform

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    @overload
    def __get__(self, obj: None, cls: type | None = None) -> 'setting[T]': ...

    @overload
    def __get__(self, obj: 'Container', cls: type | None = None) -> T: ...

    def __get__(
        self,
        obj: 'Container | None',
        cls: type | None = None,
    ) -> 'T | setting[T]':
        if obj is None:
            return self
        value = obj._settings.get(self.name, MISSING)
        return self.default if value is MISSING else value

    def __set__(self, obj: 'Container', value: T) -> None:
        obj._settings[self.name] = (
            value if self.transform is None else self.transform(value)
        )


class inherited_setting[T](setting[T]):
    """A setting that falls back to the global container instead of to its own
    default, so one `pyhtsw.configure(...)` still answers for every container."""

    @overload
    def __get__(self, obj: None, cls: type | None = None) -> 'setting[T]': ...

    @overload
    def __get__(self, obj: 'Container', cls: type | None = None) -> T: ...

    def __get__(
        self,
        obj: 'Container | None',
        cls: type | None = None,
    ) -> 'T | setting[T]':
        if obj is None:
            return self
        value = obj._settings.get(self.name, MISSING)
        if value is not MISSING:
            return value

        from pyhtsw.compiler.container import CONTAINERS

        root = CONTAINERS[0] if CONTAINERS else None
        if root is None or root is obj:
            return self.default
        return getattr(root, self.name)


UUID_PATTERN = re.compile(
    r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$',
)


def check_house_uuid(value: str | None) -> str | None:
    if value is None:
        return None
    if UUID_PATTERN.match(value) is None:
        raise ValueError(f'Not a valid house UUID: {value!r}')
    return value


def as_projects_folder(value: 'Path | str | None') -> Path | None:
    return None if value is None else Path(value).resolve()
