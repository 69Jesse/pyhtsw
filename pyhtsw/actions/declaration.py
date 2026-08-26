from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..importable import Importable


__all__ = ('resolve_declaration',)


def resolve_declaration[ImportableT: 'Importable'](
    declared: 'ImportableT | None',
    cls: type['ImportableT'],
    name: str,
    field: str,
    factory: str,
) -> 'ImportableT':
    """The importable a value object reads its declared fields from. A bare
    `Group(name)` compares equal to the one `create_group` returned, so a
    reference that never held an importable still resolves by name."""
    if declared is not None:
        return declared

    from ..container import get_current_container

    found = get_current_container().find_importable(cls.kind, name)
    if not isinstance(found, cls):
        label = cls.__name__.removesuffix('Importable')
        raise RuntimeError(
            f'{label} "{name}" was never declared, so it has no {field} to '
            f'read. Declare it with {factory}("{name}", ...), or drop the '
            f'read — a plain {label}("{name}") only names one.',
        )
    return found
