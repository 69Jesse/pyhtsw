from abc import abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Self, final

from .actions.function import Function
from .base_object import BaseObject
from .container import ContainerContextManager, ExpressionContext
from .limits import ImportableKind, fix_action_limits
from .utils.log import log

if TYPE_CHECKING:
    from .actions.item import Item
    from .container import Container
    from .execute.context import ExecutionContext
    from .expression.expression import Expression


class Block(BaseObject):
    container: 'Container'
    expressions: list['Expression']
    callback: Callable[[], None] | None
    callback_ran: bool
    # Which htsw action container this block becomes; a few limits depend on it
    # (a conditional in an event gets 40 instead of 25).
    importable_kind: ImportableKind = 'functions'
    _overflow_root_ref: 'Block | None'
    _overflow_counter: int
    _reserved_temp_numbers: set[int]

    def __init__(
        self,
        *,
        expressions: list['Expression'] | None = None,
        callback: Callable[[], None] | None = None,
    ) -> None:
        self.expressions = expressions if expressions is not None else []
        self.callback = callback
        self.callback_ran = False
        self._overflow_root_ref = None
        self._overflow_counter = 1
        self._reserved_temp_numbers = set()

    def expression_counts(
        self,
        *,
        nested: bool = False,
    ) -> dict[type['Expression'], int]:
        counts: dict[type[Expression], int] = {}
        expressions = self.expressions.copy()
        for expr in expressions:
            counts[type(expr)] = counts.get(type(expr), 0) + 1
            if not nested:
                continue
            for sub_expressions in expr.nested_expressions_refs():
                expressions.extend(sub_expressions)
        return counts

    @abstractmethod
    def equals_raw(self, other: object) -> bool:
        raise NotImplementedError

    @final
    def equals(
        self,
        other: object,
    ) -> bool:
        if not isinstance(other, Block):
            return False
        if len(self.expressions) != len(other.expressions):
            return False
        for expr1, expr2 in zip(self.expressions, other.expressions, strict=True):
            if not expr1.equals(expr2):
                return False
        return self.equals_raw(other)

    @abstractmethod
    def cloned_raw(self) -> Self:
        raise NotImplementedError

    @final
    def cloned(self) -> Self:
        clone = self.cloned_raw()
        clone.expressions = [expr.cloned() for expr in self.expressions]
        clone.callback = self.callback
        clone.callback_ran = self.callback_ran
        return clone

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(expressions={len(self.expressions)})'

    @abstractmethod
    def get_name(self) -> str:
        raise NotImplementedError()

    def is_empty(self) -> bool:
        return len(self.expressions) == 0

    def into_htsl(self) -> str:
        from .stats.temporary_stat import reserved_temp_numbers

        with reserved_temp_numbers(self._reserved_temp_numbers):
            return '\n'.join(expr.into_htsl() for expr in self.expressions)

    def maybe_run_callback(self) -> None:
        if self.callback is None or self.callback_ran:
            return
        self.callback_ran = True
        with BlockContextManager(self):
            self.callback()

    def simplify(self) -> None:
        """Merge conditionals that check the same thing and drop what cannot
        run. Both remove actions outright, so they are worth doing whether or not
        the block is anywhere near a limit."""
        from .simplify import simplify_expressions

        simplify_expressions(self.expressions, importable=self.importable_kind)

    def reorder_for_limits(self) -> None:
        """Resequence so the fixer needs as few wrapper conditionals and overflow
        functions as possible. Pure reshuffling - it only runs when the block
        would otherwise overflow, so a block that fits keeps its source order."""
        from .actions.no_optimization import optimization_enabled
        from .schedule import reorder_for_packing

        if not optimization_enabled('reorder'):
            return
        reordered = reorder_for_packing(
            self.expressions,
            importable=self.importable_kind,
        )
        if reordered is not None:
            self.expressions = reordered

    def _overflow_icon(self, root: 'Block', counter: int) -> 'Item | None':
        from .actions.item import normalize_item

        root_function = getattr(root, 'function', None)
        if root_function is None:
            return None
        icon = getattr(root_function.__htsw_importable__, 'icon', None)
        if icon is None:
            return None
        resolved = normalize_item(icon)
        return resolved.cloned(count=min(64, resolved.count + counter - 1))

    def fix_action_limits(self, container: 'Container', index: int) -> None:
        root = self._overflow_root_ref or self
        base_name = root.get_name()
        counter = self._overflow_counter + 1
        # A consumer may already own "Foo 2"; keep walking until free, and
        # let the icon's stack follow the number that actually got used.
        while container.has_importable('functions', f'{base_name} {counter}'):
            counter += 1
        function = Function(name=f'{base_name} {counter}')
        fixed, rest = fix_action_limits(
            self.expressions,
            nesting_possible=True,
            function_if_exceeds=function,
            always_in_conditional=False,
            importable=self.importable_kind,
        )
        self.expressions = fixed
        if not rest:
            return
        from .importable import FunctionImportable

        new_block = FunctionBlock(
            function=function,
            expressions=rest,
        )
        new_block._overflow_root_ref = root
        new_block._overflow_counter = counter
        new_block._reserved_temp_numbers = root._reserved_temp_numbers
        container.add_block(new_block, index=index + 1)
        overflow_importable = FunctionImportable(
            new_block,
            name=function.name,
            icon=self._overflow_icon(root, counter),
        )
        root_function = getattr(root, 'function', None)
        if root_function is not None:
            overflow_importable.module = getattr(
                root_function.__htsw_importable__,
                'module',
                None,
            )
        container.register_importable(overflow_importable)
        log(
            f'Created a new function \x1b[38;2;255;0;0m"{function.name}"\x1b[0m to avoid hitting the action limit in block \x1b[38;2;0;255;0m"{self.get_name()}"\x1b[0m',
        )

    def finalize(self, container: 'Container', index: int) -> None:
        self.maybe_run_callback()
        # An overflow block holds a tail that `fix_action_limits` carved off an
        # already-finalized block, so its expressions are finalized too — a
        # second pass is a no-op. Skipping it avoids quadratic finalize work
        if self._overflow_root_ref is None:
            self._reserved_temp_numbers = container.finalize_expressions(
                self.expressions,
            )
        self.simplify()
        if not self.container.ignore_action_limits:
            self.reorder_for_limits()
            self.fix_action_limits(container, index)

    def execute_all_expressions(self, context: 'ExecutionContext') -> None:
        from .execute.signal import ExitSignal, PauseSignal
        from .stats.temporary_stat import reserved_temp_numbers

        self.maybe_run_callback()
        block_reserved = context.finalize_expressions(self.expressions)

        with reserved_temp_numbers(block_reserved):
            flat: list[Expression] = []
            for expression in self.expressions:
                flat.extend(expression.into_executable_expressions())

            try:
                context.run_expressions(flat)
            except ExitSignal:
                pass
            except PauseSignal as sig:
                context.schedule_continuation(sig.continuation, sig.ticks)

    def execute(self, context: 'ExecutionContext') -> None:
        pass  # Do nothing on purpose, since most of the time this is but a definition


@final
class GlobalBlock(Block):
    def equals_raw(self, other: object) -> bool:
        return isinstance(other, GlobalBlock)

    def cloned_raw(self) -> Self:
        return self.__class__()

    def get_name(self) -> str:
        return 'Rename Me !!!'

    def execute(self, context: 'ExecutionContext') -> None:
        self.execute_all_expressions(context)


@final
class FunctionBlock(Block):
    function: Function

    def __init__(
        self,
        function: Function,
        *,
        expressions: list['Expression'] | None = None,
        callback: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(
            expressions=expressions,
            callback=callback,
        )
        self.function = function
        assert self.function.block is None
        self.function.block = self

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, FunctionBlock):
            return False
        return self.function == other.function

    def cloned_raw(self) -> Self:
        return self.__class__(function=self.function)

    def get_name(self) -> str:
        return self.function.name


@final
class NamedBlock(Block):
    """An action list owned by a non-function importable (item/region/menu/npc)."""

    _name: str

    def __init__(
        self,
        name: str,
        *,
        expressions: list['Expression'] | None = None,
        callback: Callable[[], None] | None = None,
        importable_kind: ImportableKind = 'functions',
    ) -> None:
        super().__init__(expressions=expressions, callback=callback)
        self._name = name
        self.importable_kind = importable_kind

    def equals_raw(self, other: object) -> bool:
        return isinstance(other, NamedBlock) and other._name == self._name

    def cloned_raw(self) -> Self:
        return self.__class__(self._name, importable_kind=self.importable_kind)

    def get_name(self) -> str:
        return self._name


@final
class BlockContextManager(ContainerContextManager):
    block: Block

    def __init__(self, block: Block) -> None:
        self.block = block

    def create_context(self) -> ExpressionContext:
        return ExpressionContext(
            parent_expression=None,
            expressions_ref=self.block.expressions,
            add_expression_to_container=False,
        )
