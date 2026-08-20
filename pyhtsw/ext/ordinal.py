from ..actions.conditional.statements import IfAll
from ..checkable import Checkable
from ..editable import Editable
from ..stats.temporary_stat import TemporaryStat

__all__ = ('set_ordinal_inline',)


def set_ordinal_inline(
    checking_stat: Checkable,
    output_stat: Editable,
) -> None:
    """Set ``output_stat`` to the English ordinal suffix ('st'/'nd'/'rd'/'th')
    for ``checking_stat``."""
    last_two_digits = TemporaryStat().as_long()
    last_digit = TemporaryStat().as_long()
    scratch = TemporaryStat().as_long()

    def assign_modulo(into: TemporaryStat, value: Checkable, divisor: int) -> None:
        into.value = value
        scratch.value = into
        scratch.value //= divisor
        scratch.value *= divisor
        into.value -= scratch

    assign_modulo(last_two_digits, checking_stat, 100)
    assign_modulo(last_digit, last_two_digits, 10)

    output_stat.value = 'th'
    # Each branch only needs to exclude its own teen: a last digit of 1 rules
    # out 12/13 by itself, and the digit checks are mutually exclusive.
    with IfAll(~(last_two_digits == 11), last_digit == 1):
        output_stat.value = 'st'
    with IfAll(~(last_two_digits == 12), last_digit == 2):
        output_stat.value = 'nd'
    with IfAll(~(last_two_digits == 13), last_digit == 3):
        output_stat.value = 'rd'
    # else: 'th' (already set)
