from abc import abstractmethod
from collections.abc import Callable, Generator
from typing import TYPE_CHECKING, ClassVar, Self, final

from pyhtsw.base_object import BaseObject
from pyhtsw.container import Container
from pyhtsw.registry import ConditionMeta
from pyhtsw.utils.log import log

if TYPE_CHECKING:
    from pyhtsw.checkable import Checkable
    from pyhtsw.execute.context import ExecutionContext
    from pyhtsw.expression.housing_type import HousingType
    from pyhtsw.stats.stat import Stat


__all__ = ('Condition',)


class Condition(BaseObject):
    htsw_meta: ClassVar[ConditionMeta] = ConditionMeta()

    inverted: bool = False
    __clone_extra__: ClassVar[tuple[str, ...]] = ('inverted',)

    @abstractmethod
    def into_htsl_raw(self) -> str:
        raise NotImplementedError

    @final
    def into_htsl(self) -> str:
        return ('!' * self.inverted) + self.into_htsl_raw()

    def equals_raw(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.fields_equal(other)

    @final
    def equals(self, other: object) -> bool:
        if not isinstance(other, Condition):
            return False
        return self.inverted == other.inverted and self.equals_raw(other)

    def __invert__(self) -> Self:
        return self.cloned(inverted=not self.inverted)

    def raw_evaluate(self, context: 'ExecutionContext') -> bool:
        log(
            f'No execution implemented for condition \x1b[38;2;255;0;0m"{self!r}"\x1b[0m, returning False',
        )
        return False

    @final
    def evaluate(self, context: 'ExecutionContext') -> bool:
        if context.verbose:
            log(f'Executing condition \x1b[38;2;255;0;0m"{self!r}"\x1b[0m')
        value = self.raw_evaluate(context)
        if self.inverted:
            value = not value
        return value

    def related_debug_parts(self) -> list['Checkable | HousingType']:
        return []

    def referenced_importables(self) -> list[tuple[str, str]]:
        """`(kind, name)` of every importable this condition refers to, surfaced
        through the owning `ConditionalExpression`. See `Expression`."""
        return []

    def finalize(self, container: Container) -> None:
        self.into_htsl()

    def _set_stat(self, key: str, value: 'Stat') -> None:
        setattr(self, key, value)

    def get_all_stats_used(
        self,
    ) -> Generator[tuple['Stat', Callable[['Stat'], None]]]:
        from pyhtsw.stats.stat import Stat

        for key, value in vars(self).items():
            if isinstance(value, Stat):
                yield (value, lambda new, _k=key: self._set_stat(_k, new))
