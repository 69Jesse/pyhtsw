from collections.abc import Callable, Sequence

from pyhtsw.actions.flow import IfAll
from pyhtsw.editable import Editable, HousingType
from pyhtsw.expression.condition.condition import Condition
from pyhtsw.ext.array_read_write import MaybeSequence
from pyhtsw.ext.stack_queue import IfPresent, _SlotContainerBase
from pyhtsw.helpers import chunked
from pyhtsw.stats.temporary_stat import TemporaryStat

__all__ = ('Vector',)

type Where = Callable[..., Condition | Sequence[Condition]]

# A take's branch holds the copy out, the shift of every slot above, the
# counter and the flag; Housing allows 25 changes per list.
_BRANCH_LIMIT = 25


class Vector(_SlotContainerBase):
    """An ordered, bounded list over one Stat per slot and column: `push` at
    the back, and `take_first` to pull out the first slot a condition matches
    and close the gap. Slots past `counter` are stale, never cleared, and never
    read."""

    def push(
        self,
        value: MaybeSequence[Editable | HousingType],
        *,
        when: Sequence[Condition] = (),
    ) -> None:
        """`when` gates the push: every conditional it emits also requires
        those conditions, which is what lets a push sit in a list after a
        function that decided whether there is anything to push."""
        if not when:
            self._push_back(value)
            return
        values = self._normalize_values(value, label='push')
        if self.on_overflow == 'override_oldest':
            with chunked(IfAll(*when, self.counter == self.capacity)):
                self._shift_down(None)
                self.counter.value -= 1
        elif self.on_overflow == 'override_newest':
            with IfAll(*when, self.counter == self.capacity):
                self._write_at_slot(self.capacity - 1, values)
        for i in range(self.capacity - 1, -1, -1):
            with IfAll(*when, self.counter == i):
                self._write_at_slot(i, values)
                self.counter.value += 1

    def take_first(
        self,
        *,
        where: Where,
        output: MaybeSequence[Editable],
        if_present: IfPresent = None,
        if_absent: IfPresent = None,
    ) -> None:
        """`where` gets one slot's stats, one per column, and returns the
        condition(s) that slot has to meet. The first match is copied into
        `output`, everything above it shifts down, and `if_present` or
        `if_absent` runs afterwards, outside the search."""
        outputs = self._normalize_outputs(output, label='take_first')
        worst = self.width * self.capacity + 2
        if worst > _BRANCH_LIMIT:
            raise ValueError(
                f'{type(self).__name__}.take_first: capacity {self.capacity} x '
                f'width {self.width} needs {worst} changes in one branch, over '
                f'the {_BRANCH_LIMIT} Housing allows; shrink one of them',
            )

        found = TemporaryStat().as_long()
        found.value = 0
        for i in range(self.capacity):
            conditions = where(*self.holders[i])
            if isinstance(conditions, Condition):
                conditions = (conditions,)
            with IfAll(self.counter > i, found == 0, *conditions):
                for w in range(self.width):
                    outputs[w].value = self.holders[i][w]
                for j in range(i, self.capacity - 1):
                    for w in range(self.width):
                        self.holders[j][w].value = self.holders[j + 1][w]
                self.counter.value -= 1
                found.value = 1
        if if_present is not None:
            with IfAll(found == 1):
                if_present()
        if if_absent is not None:
            with IfAll(found == 0):
                if_absent()
