from collections.abc import Callable, Sequence
from typing import Literal

from pyhtsw.actions.flow import Else, IfAll
from pyhtsw.checkable import Checkable
from pyhtsw.directives.preserved import Preserved
from pyhtsw.directives.strict_order import StrictOrder
from pyhtsw.editable import HousingType
from pyhtsw.expression.housing_type import NumericHousingType
from pyhtsw.ext.array_read_write import MaybeSequence, assert_same_widths, into_sequence
from pyhtsw.helpers import chunked
from pyhtsw.internal_type import InternalType
from pyhtsw.stats.stat import Stat
from pyhtsw.stats.temporary_stat import TemporaryStat

__all__ = ('SortedTopN',)


type Order = Literal['ascending', 'descending']

type OnRank = Callable[[], None] | None

KEY_LIMIT = 1 << 62


class SortedTopN:
    """A fixed-size array of slots kept sorted by one of its columns.

    Slot order is rank order, so the stats are the display: point a hologram
    (or a scoreboard, or a menu) straight at slot 0..N and it is always
    current, because there is nothing to render.
    """

    slots: Sequence[tuple[Stat, ...]]
    key_column: int
    identity_column: int | None
    order: Order
    empty: tuple[HousingType, ...] | None

    @property
    def capacity(self) -> int:
        return len(self.slots)

    @property
    def width(self) -> int:
        return len(self.slots[0])

    def __init__(
        self,
        *,
        slots: Sequence[MaybeSequence[Stat]],
        key_column: int = -1,
        identity_column: int | None = None,
        order: Order = 'ascending',
        empty: MaybeSequence[HousingType] | None = None,
    ) -> None:
        if not slots:
            raise ValueError('SortedTopN: slots must be non-empty')

        groups = [tuple(into_sequence(g)) for g in slots]
        width = assert_same_widths(groups)

        key_column = range(width)[key_column]
        if identity_column is not None:
            identity_column = range(width)[identity_column]

        seen: list[Stat] = []
        for group in groups:
            for stat in group:
                for prior in seen:
                    if stat.is_same_stat(prior):
                        raise ValueError(
                            f'SortedTopN: holder stat {stat!r} is duplicated. '
                            f'Each slot needs its own Stat.',
                        )
                seen.append(stat)

        for group in groups:
            if group[key_column].internal_type is not InternalType.LONG:
                raise ValueError(
                    f'SortedTopN: the key column ({key_column}) must be LONG, '
                    f'got {group[key_column].internal_type}. Store a raw '
                    f'sortable number there and keep the display text in '
                    f'another column.',
                )

        empty_values: tuple[HousingType, ...] | None = None
        if empty is not None:
            empty_values = tuple(into_sequence(empty))
            if len(empty_values) != width:
                raise ValueError(
                    f'SortedTopN: empty has {len(empty_values)} value(s), '
                    f'expected {width} (one per column)',
                )

        self.slots = [tuple(s.with_auto_unset(False) for s in g) for g in groups]
        self.key_column = key_column
        self.identity_column = identity_column
        self.order = order
        self.empty = empty_values

        self.rank = TemporaryStat().as_long()
        self._difference = TemporaryStat().as_long()
        self._found_index = TemporaryStat().as_long()
        self._found_key = TemporaryStat().as_long()

    @property
    def sentinel(self) -> int:
        return KEY_LIMIT if self.order == 'ascending' else -KEY_LIMIT

    def _normalize(
        self,
        values: MaybeSequence[Checkable | HousingType],
        *,
        label: str,
    ) -> list[Checkable | HousingType]:
        listed = list(into_sequence(values))
        if len(listed) != self.width:
            raise ValueError(
                f'SortedTopN.{label}: got {len(listed)} value(s), expected '
                f'{self.width} (one per column)',
            )
        return listed

    def seed(self) -> None:
        """Fill every slot with the empty-row values and a sentinel key."""
        if self.empty is None:
            raise ValueError(
                'SortedTopN.seed: pass `empty=` to the constructor to use seed()',
            )
        sentinel = self.sentinel
        with Preserved():
            for slot in self.slots:
                for w in range(self.width):
                    slot[w].value = sentinel if w == self.key_column else self.empty[w]

    def insert(
        self,
        values: MaybeSequence[Checkable | HousingType],
        *,
        identity: Checkable | HousingType | None = None,
        if_entered: OnRank = None,
        if_missed: OnRank = None,
    ) -> None:
        """Place `values` at its sorted position, shifting the tail down.

        `identity` replaces this player's existing row instead of adding a
        second one, and is ignored when their current row is already better.
        Neither callback may open a conditional of its own.
        """
        listed = self._normalize(values, label='insert')
        key = listed[self.key_column]
        if isinstance(key, str):
            raise ValueError(
                f'SortedTopN.insert: the key column ({self.key_column}) must '
                f'be a number, got {key!r}',
            )
        if isinstance(key, int) and not 0 <= key < KEY_LIMIT:
            raise ValueError(
                f'SortedTopN.insert: key {key} is outside [0, {KEY_LIMIT}) - '
                f'the sign-bit rank count would overflow',
            )
        if identity is not None and self.identity_column is None:
            raise ValueError(
                'SortedTopN.insert: pass `identity_column=` to the constructor '
                'to insert with an identity',
            )

        deduped = identity is not None
        self._locate(identity)
        self._compute_rank(key, deduped=deduped)
        self._shift_and_write(listed, deduped=deduped)

        if if_entered is not None or if_missed is not None:
            with IfAll(self.rank < self.capacity):
                if if_entered is not None:
                    if_entered()
            if if_missed is not None:
                with Else:
                    if_missed()

    def _locate(self, identity: Checkable | HousingType | None) -> None:
        if identity is None:
            return
        assert self.identity_column is not None
        self._found_index.value = self.capacity - 1
        self._found_key.value = self.sentinel
        for i, slot in enumerate(self.slots):
            with IfAll(slot[self.identity_column] == identity):
                self._found_index.value = i
                self._found_key.value = slot[self.key_column]

    def _compute_rank(
        self,
        key: Checkable | NumericHousingType,
        *,
        deduped: bool,
    ) -> None:
        rank = self.rank
        difference = self._difference
        ascending = self.order == 'ascending'

        rank.value = 0
        for slot in self.slots:
            if ascending:
                difference.value = slot[self.key_column]
                difference.value -= key
            else:
                difference.value = key
                difference.value -= slot[self.key_column]
            difference.value -= 1
            difference.logical_rshift(63).write()
            rank.value += difference

        if deduped:
            better = key >= self._found_key if ascending else key <= self._found_key
            with IfAll(better):
                rank.value = self.capacity

    def _shift_and_write(
        self,
        values: Sequence[Checkable | HousingType],
        *,
        deduped: bool,
    ) -> None:
        with StrictOrder():
            for i in range(self.capacity - 1, 0, -1):
                conditions = [self.rank < i]
                if deduped:
                    conditions.append(self._found_index >= i)
                with chunked(IfAll(*conditions)):
                    for w in range(self.width):
                        self.slots[i][w].value = self.slots[i - 1][w]

            for r, slot in enumerate(self.slots):
                with chunked(IfAll(self.rank == r)):
                    for w in range(self.width):
                        slot[w].value = values[w]
