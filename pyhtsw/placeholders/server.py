import re
from typing import final

from pyhtsw.compiler.registry import ActionMeta
from pyhtsw.compiler.schedule import Effects
from pyhtsw.execute.backend_type import BackendType
from pyhtsw.internal_type import InternalType
from pyhtsw.placeholders.base import PlaceholderCheckable

__all__ = (
    'ServerNamePlaceholder',
    'ServerName',
    'ServerShortNamePlaceholder',
    'ServerShortName',
)


@final
class ServerNamePlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%server.name%')),
    pattern_factory=lambda _: ServerName,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%server.name%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''


ServerName = ServerNamePlaceholder()


@final
class ServerShortNamePlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%server.shortname%')),
    pattern_factory=lambda _: ServerShortName,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%server.shortname%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''


ServerShortName = ServerShortNamePlaceholder()
