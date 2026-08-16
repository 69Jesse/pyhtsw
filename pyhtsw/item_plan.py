from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .actions.item import Item
    from .block import Block
    from .expression.expression import Expression
    from .importable import Importable, ItemImportable

__all__ = ('ItemPlan', 'plan_items', 'promoted_importables')


class ItemPlanEntry:
    __slots__ = ('declared', 'item', 'name', 'owner_module', 'referenced')

    def __init__(
        self,
        *,
        name: str,
        owner_module: str | None,
        item: 'Item',
        declared: bool,
        referenced: bool,
    ) -> None:
        self.name = name
        self.owner_module = owner_module
        self.item = item
        self.declared = declared
        self.referenced = referenced

    @property
    def needs_importable(self) -> bool:
        return self.referenced and not self.declared

    def __repr__(self) -> str:
        return f'ItemPlanEntry<{self.name!r} owner={self.owner_module}>'


class ItemPlan:
    entries: dict[str, ItemPlanEntry]

    def __init__(self, entries: dict[str, ItemPlanEntry]) -> None:
        self.entries = entries

    def lookup(self, item: 'Item') -> ItemPlanEntry | None:
        return self.entries.get(item.into_snbt())

    def to_promote(self) -> list[ItemPlanEntry]:
        return sorted(
            (entry for entry in self.entries.values() if entry.needs_importable),
            key=lambda entry: entry.name,
        )


class _Group:
    __slots__ = (
        'declared_module',
        'declared_name',
        'items',
        'modules',
        'promotable',
        'referenced',
    )

    def __init__(self) -> None:
        self.items: list[Item] = []
        self.modules: set[str | None] = set()
        self.referenced = False
        self.promotable = True
        self.declared_name: str | None = None
        self.declared_module: str | None = None

    def add(self, item: 'Item', *, referenced: bool) -> None:
        self.items.append(item)
        self.modules.add(item.__htsw_module__)
        self.referenced = self.referenced or referenced
        self.promotable = self.promotable and item._promotable


def _iter_item_fields(obj: object) -> Iterator['Item | type[Item]']:
    from .actions.item import Item
    from .expression.condition.condition import Condition

    for value in vars(obj).values():
        candidates = value if isinstance(value, list | tuple) else (value,)
        for candidate in candidates:
            if isinstance(candidate, Item):
                yield candidate
            elif isinstance(candidate, type) and issubclass(candidate, Item):
                yield candidate
            elif isinstance(candidate, Condition):
                yield from _iter_item_fields(candidate)


def _walk_expressions(expressions: list['Expression']) -> Iterator['Expression']:
    for expression in expressions:
        yield expression
        for nested in expression.nested_expressions_refs():
            yield from _walk_expressions(nested)


def _owner_module(modules: set[str | None]) -> str | None:
    named = sorted(module for module in modules if module and module != '__main__')
    return named[0] if named else None


def _sized(base: str, count: int) -> str:
    if count <= 1 or base.endswith(f' x{count}'):
        return base
    return f'{base} x{count}'


def _moduled(base: str, module: str | None) -> str:
    segment = module.rsplit('.', 1)[-1].replace('_', ' ') if module else ''
    return f'{base} ({segment})' if segment else base


# Tiebreakers to try, cheapest first. Each says what actually differs between
# the items sharing a name: the stack size (one display name covers every size
# of an item), then the owning module (the same item again as a shop display,
# as a menu icon), then both.
_LABELLERS: tuple[Callable[[str, int, str | None], str], ...] = (
    lambda base, _count, _module: base,
    lambda base, count, _module: _sized(base, count),
    lambda base, _count, module: _moduled(base, module),
    lambda base, count, module: _moduled(_sized(base, count), module),
)


def _allocate_bucket(
    base: str,
    members: list[tuple[int, str | None]],
    used: set[str],
) -> list[str]:
    labelled = [
        [labeller(base, count, module) for count, module in members]
        for labeller in _LABELLERS
    ]
    for names in labelled:
        if len(set(names)) == len(names) and not any(name in used for name in names):
            used.update(names)
            return names

    # Nothing separates them cleanly. Number off whichever labelling got closest
    # (ties go to the cheapest), so seven bows differing only by enchantment stay
    # "Bow", "Bow 2", ... instead of carrying a module that separates nothing.
    names = []
    for candidate in max(labelled, key=lambda option: len(set(option))):
        if candidate in used:
            number = 2
            while f'{candidate} {number}' in used:
                number += 1
            candidate = f'{candidate} {number}'
        used.add(candidate)
        names.append(candidate)
    return names


def _collect(
    blocks: list['Block'],
    importables: list['Importable'],
) -> dict[str, _Group]:
    from .importable import ItemImportable, MenuImportable, NpcImportable

    groups: dict[str, _Group] = {}

    def group_for(item: 'Item') -> _Group:
        return groups.setdefault(item.into_snbt(), _Group())

    def add(value: 'Item | type[Item] | None', *, referenced: bool) -> None:
        if value is None:
            return
        # A declared subclass is referenced by its class name and its canonical
        # instance arrives with its ItemImportable; a throwaway `cls()` here
        # would only add an unstampable duplicate.
        if isinstance(value, type):
            return
        group_for(value).add(value, referenced=referenced)

    # Declared items first so their names are the ones that survive a collision.
    for importable in sorted(
        (imp for imp in importables if isinstance(imp, ItemImportable)),
        key=lambda imp: imp.name,
    ):
        group = group_for(importable.item)
        group.add(importable.item, referenced=False)
        if group.declared_name is None:
            group.declared_name = importable.name
            group.declared_module = importable.module

    for importable in importables:
        if isinstance(importable, MenuImportable):
            for slot in importable.slots:
                add(slot.item, referenced=False)
        elif isinstance(importable, NpcImportable) and importable.equipment is not None:
            for slot_name in importable.equipment.SLOTS:
                add(getattr(importable.equipment, slot_name), referenced=False)

    for block in blocks:
        for expression in _walk_expressions(block.expressions):
            for value in _iter_item_fields(expression):
                add(value, referenced=True)

    return groups


def plan_items(
    blocks: list['Block'],
    importables: list['Importable'],
) -> ItemPlan:
    groups = _collect(blocks, importables)

    used: set[str] = {
        group.declared_name
        for group in groups.values()
        if group.declared_name is not None
    }
    entries: dict[str, ItemPlanEntry] = {}

    def record(snbt: str, group: _Group, name: str, module: str | None) -> None:
        entry = ItemPlanEntry(
            name=name,
            owner_module=module,
            item=group.items[0],
            declared=group.declared_name is not None,
            referenced=group.referenced and group.promotable,
        )
        entries[snbt] = entry
        # Every item gets a name so its .snbt file reads as something, but only
        # one that actually ends up in import.json may be referenced by it — an
        # action naming an item htsw cannot find is a hard import error.
        reference = name if entry.declared or entry.needs_importable else None
        for item in group.items:
            item._reference_name = reference
            item._owner_module = module

    for snbt, group in groups.items():
        if group.declared_name is not None:
            record(snbt, group, group.declared_name, group.declared_module)

    # Content-determined order, so which of two colliding items keeps the bare
    # name never depends on where they happen to sit in the source.
    buckets: dict[str, list[tuple[str | None, str]]] = {}
    for snbt, group in groups.items():
        if group.declared_name is not None:
            continue
        buckets.setdefault(group.items[0].derived_name(), []).append(
            (_owner_module(group.modules), snbt),
        )

    for base in sorted(buckets):
        members = sorted(buckets[base], key=lambda member: (member[0] or '', member[1]))
        names = _allocate_bucket(
            base,
            [(groups[snbt].items[0].count, module) for module, snbt in members],
            used,
        )
        for (module, snbt), name in zip(members, names, strict=True):
            record(snbt, groups[snbt], name, module)

    return ItemPlan(entries)


def promoted_importables(plan: ItemPlan) -> list['ItemImportable']:
    from .importable import ItemImportable

    promoted: list[ItemImportable] = []
    for entry in plan.to_promote():
        importable = ItemImportable(name=entry.name, item=entry.item)
        importable.module = entry.owner_module
        promoted.append(importable)
    return promoted
