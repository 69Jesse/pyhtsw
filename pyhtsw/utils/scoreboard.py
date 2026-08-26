import itertools
from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING, NamedTuple, Union

from pyhtsw.utils.placeholders import get_placeholder_parts
from pyhtsw.utils.warn import warn

if TYPE_CHECKING:
    from pyhtsw.checkable import Checkable

__all__ = (
    'FIELD_MAX_LENGTH',
    'KNOWN_GOOD_SOURCE_LENGTH',
    'MAX_INSERTED_LENGTH',
    'HypixelSplit',
    'fix_scoreboard_line',
    'number_lengths',
    'simulate_hypixel_split',
)

# Per scoreboard team field, and certain. Whatever the editor caps its input at
# is not: 45 characters of source are accepted in game, and the render window
# hides anything that would prove a limit beyond that.
FIELD_MAX_LENGTH: int = 16
KNOWN_GOOD_SOURCE_LENGTH: int = 45

# Padding only ever has to push text across a 16-character window, and a
# re-emit is a color plus at most five formats.
MAX_INSERTED_LENGTH: int = 24

COLOR_CODES: frozenset[str] = frozenset('0123456789abcdef')
FORMAT_CODES: frozenset[str] = frozenset('klmno')
RESET_CODE: str = 'r'
DEFAULT_COLOR: str = 'f'

# Stand-ins for a resolved placeholder; dirty ones poison the format state.
CLEAN_FILLER: str = '\x02'
DIRTY_FILLER: str = '\x01'

MAX_COMBINATIONS: int = 4096

# Stood in for a placeholder that lands too late to move the seam, and so never
# had to be declared. It only feeds the truncation estimate.
ASSUMED_LENGTH: int = 1

PlaceholderKey = Union[str, 'Checkable']


class State(NamedTuple):
    color: str | None = None
    formats: tuple[str, ...] = ()
    unknown: bool = False

    @property
    def bold(self) -> bool:
        return self.unknown or 'l' in self.formats


class HypixelSplit(NamedTuple):
    prefix: str
    suffix: str
    entry_state: State
    dropped: str

    @property
    def has_gap(self) -> bool:
        return bool(self.suffix) and self.entry_state.bold


def _is_code(char: str) -> bool:
    return char in COLOR_CODES or char in FORMAT_CODES or char == RESET_CODE


def _starts_with_color(text: str) -> bool:
    return (
        len(text) >= 2
        and text[0] == '§'
        and (text[1] in COLOR_CODES or text[1] == RESET_CODE)
    )


def _apply(state: State, code: str) -> State:
    if code in COLOR_CODES:
        return State(code, ())
    if code == RESET_CODE:
        return State()
    if code in state.formats:
        return state
    return State(state.color, state.formats + (code,), state.unknown)


def _states(text: str) -> list[State]:
    states: list[State] = [State()]
    state = State()
    index = 0
    while index < len(text):
        char = text[index]
        if char == '§' and index + 1 < len(text) and _is_code(text[index + 1]):
            states.append(state)
            state = _apply(state, text[index + 1])
            states.append(state)
            index += 2
            continue
        if char == DIRTY_FILLER:
            state = State(unknown=True)
        states.append(state)
        index += 1
    return states


def _last_colors(text: str) -> str:
    result = ''
    for index in range(len(text) - 2, -1, -1):
        if text[index] != '§':
            continue
        code = text[index + 1]
        if code in COLOR_CODES or code == RESET_CODE:
            return f'§{code}{result}'
        if code in FORMAT_CODES:
            result = f'§{code}{result}'
    return result


def _normalize(text: str) -> tuple[str, list[int]]:
    out: list[str] = []
    mapping: list[int] = []
    index = 0
    while index < len(text):
        if text[index] == '&' and index + 1 < len(text):
            following = text[index + 1]
            if following == '&':
                out.append('&')
                mapping.append(index)
                index += 2
                continue
            if _is_code(following):
                out.append('§')
                mapping.append(index)
                out.append(following)
                mapping.append(index + 1)
                index += 2
                continue
        out.append(text[index])
        mapping.append(index)
        index += 1
    mapping.append(len(text))
    return ''.join(out), mapping


def simulate_hypixel_split(line: str) -> HypixelSplit:
    """Reproduce how Hypixel cuts a scoreboard line around its entry emoji.

    The line becomes a legacy scoreboard team: a prefix, the per-line entry
    name (an emoji whose glyph is blank), and a suffix, each field capped at
    ``FIELD_MAX_LENGTH``. ``dropped`` is the text the caps discarded.
    """
    text, _ = _normalize(line)
    states = _states(text)
    if len(text) <= FIELD_MAX_LENGTH:
        return HypixelSplit(text, '', states[len(text)], '')

    cut = FIELD_MAX_LENGTH
    if text[cut - 1] == '§':
        cut -= 1
    prefix = text[:cut]
    rest = text[cut:]
    if not _starts_with_color(rest):
        rest = _last_colors(prefix) + rest
    return HypixelSplit(
        prefix,
        rest[:FIELD_MAX_LENGTH],
        states[cut],
        rest[FIELD_MAX_LENGTH:],
    )


def _key_strings(key: PlaceholderKey) -> tuple[str, ...]:
    if isinstance(key, str):
        return (key,)
    strings = {key.into_inside_string()}
    try:
        strings.add(key.into_inside_string(include_fallback_value=False))  # type: ignore[call-arg]
    except TypeError:
        pass
    return tuple(strings)


def _placeholder_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    index = 0
    for position, part in enumerate(get_placeholder_parts(text)):
        if position % 2 == 1 and part:
            spans.append((index, index + len(part)))
        index += len(part)
    return spans


def _insertion_points(text: str, spans: list[tuple[int, int]]) -> list[int]:
    forbidden: set[int] = set()
    index = 0
    while index < len(text):
        if text[index] == '§' and index + 1 < len(text) and _is_code(text[index + 1]):
            forbidden.add(index + 1)
            index += 2
            continue
        index += 1
    for start, end in spans:
        forbidden.update(range(start + 1, end))
    return [i for i in range(len(text) + 1) if i not in forbidden]


def _pad(state: State) -> str | None:
    if state.unknown:
        return None
    if state.formats:
        return f'§{state.formats[-1]}'
    if state.color is not None:
        return f'§{state.color}'
    return None


def _reemit(state: State) -> str | None:
    if state.unknown:
        return None
    return f'§{state.color or DEFAULT_COLOR}' + ''.join(
        f'§{code}' for code in state.formats
    )


def _pads(state: State, budget: int) -> list[str]:
    pad = _pad(state)
    if pad is None:
        return []
    return [pad * count for count in range(1, (budget // len(pad)) + 1)]


def _payloads(state: State, budget: int) -> list[str]:
    if budget < 2:
        return []
    payloads = _pads(state, budget)
    reemit = _reemit(state)
    if reemit is not None:
        payloads.extend(
            pad + reemit
            for pad in ['', *_pads(state, budget - len(reemit))]
            if len(pad) + len(reemit) <= budget
        )
    return payloads


def _resolve(
    template: str,
    spans: list[tuple[int, int]],
    lengths: tuple[int, ...],
    dirty: tuple[bool, ...],
) -> str:
    out: list[str] = []
    last = 0
    for (start, end), length, is_dirty in zip(spans, lengths, dirty, strict=True):
        out.append(template[last:start])
        out.append((DIRTY_FILLER if is_dirty else CLEAN_FILLER) * length)
        last = end
    out.append(template[last:])
    return ''.join(out)


def _render(text: str) -> tuple[tuple[str, State], ...]:
    states = _states(text)
    out: list[tuple[str, State]] = []
    index = 0
    while index < len(text):
        if text[index] == '§' and index + 1 < len(text) and _is_code(text[index + 1]):
            index += 2
            continue
        out.append((text[index], states[index + 1]))
        index += 1
    return tuple(out)


def _same_color(left: str | None, right: str | None) -> bool:
    return (left or DEFAULT_COLOR) == (right or DEFAULT_COLOR)


def _renders_match(
    left: tuple[tuple[str, State], ...],
    right: tuple[tuple[str, State], ...],
) -> bool:
    if len(left) != len(right):
        return False
    for (left_char, left_state), (right_char, right_state) in zip(
        left,
        right,
        strict=True,
    ):
        if left_char != right_char:
            return False
        if left_state.unknown or right_state.unknown:
            continue
        if not _same_color(left_state.color, right_state.color):
            return False
        if set(left_state.formats) != set(right_state.formats):
            return False
    return True


def _splice(text: str, insertions: tuple[tuple[int, str], ...]) -> str:
    for point, payload in sorted(insertions, reverse=True):
        text = text[:point] + payload + text[point:]
    return text


def _shift_spans(
    spans: list[tuple[int, int]],
    insertions: tuple[tuple[int, str], ...],
) -> list[tuple[int, int]]:
    shifted: list[tuple[int, int]] = []
    for start, end in spans:
        offset = sum(len(payload) for point, payload in insertions if point <= start)
        shifted.append((start + offset, end + offset))
    return shifted


class _Problem(NamedTuple):
    template: str
    spans: list[tuple[int, int]]
    dirty: tuple[bool, ...]
    combinations: tuple[tuple[int, ...], ...]
    baseline: tuple[tuple[tuple[str, State], ...], ...]

    def check(self, insertions: tuple[tuple[int, str], ...]) -> bool:
        template = _splice(self.template, insertions)
        spans = _shift_spans(self.spans, insertions)
        for lengths, baseline in zip(
            self.combinations,
            self.baseline,
            strict=True,
        ):
            resolved = _resolve(template, spans, lengths, self.dirty)
            if simulate_hypixel_split(resolved).has_gap:
                return False
            if not _renders_match(_render(resolved), baseline):
                return False
        return True

    def worst_dropped(self, insertions: tuple[tuple[int, str], ...]) -> int:
        template = _splice(self.template, insertions)
        spans = _shift_spans(self.spans, insertions)
        return max(
            len(
                simulate_hypixel_split(
                    _resolve(template, spans, lengths, self.dirty),
                ).dropped,
            )
            for lengths in self.combinations
        )


def _candidates(
    points: list[int],
    states: list[State],
    budget: int,
) -> list[tuple[tuple[int, str], ...]]:
    singles: list[tuple[tuple[int, str], ...]] = [
        ((point, payload),)
        for point in points
        for payload in _payloads(states[point], budget)
    ]

    # Padding early, re-emitting at the seam: what it takes to push a
    # placeholder past the seam and still land a color code on it.
    pairs: list[tuple[tuple[int, str], ...]] = []
    for first in points:
        for pad in _pads(states[first], budget - 2):
            for second in points:
                if second <= first:
                    continue
                reemit = _reemit(states[second])
                if reemit is None or len(pad) + len(reemit) > budget:
                    continue
                pairs.append(((first, pad), (second, reemit)))

    # Latest insertion wins ties, which leaves as much of the line as possible
    # ahead of the seam untouched.
    candidates = singles + pairs
    candidates.sort(
        key=lambda insertions: (
            sum(len(payload) for _, payload in insertions),
            tuple(-point for point, _ in insertions),
        ),
    )
    return candidates


def _reaching_the_seam(
    template: str,
    spans: list[tuple[int, int]],
    declared: dict[str, tuple[int, ...]],
) -> list[str]:
    # The seam is decided by the first FIELD_MAX_LENGTH resolved characters, so
    # a placeholder that cannot start before them cannot move it. Resolved
    # starts only grow along the line, so the first one past is the last check.
    missing: list[str] = []
    offset = 0
    for start, end in spans:
        if start - offset > FIELD_MAX_LENGTH:
            break
        token = template[start:end]
        if token not in declared:
            missing.append(token)
        offset += len(token) - min(declared.get(token, (ASSUMED_LENGTH,)))
    return missing


def _collect(
    placeholders: Mapping[PlaceholderKey, int | Iterable[int]] | None,
    dirty: Iterable[PlaceholderKey],
) -> tuple[dict[str, tuple[int, ...]], set[str]]:
    lengths: dict[str, tuple[int, ...]] = {}
    for key, value in (placeholders or {}).items():
        declared = (value,) if isinstance(value, int) else tuple(value)
        if not declared:
            raise ValueError(f'no lengths declared for placeholder {key!r}')
        if any(length < 0 for length in declared):
            raise ValueError(f'negative length declared for placeholder {key!r}')
        for string in _key_strings(key):
            lengths[string] = declared
    dirty_strings = {string for key in dirty for string in _key_strings(key)}
    return lengths, dirty_strings


def fix_scoreboard_line(
    text: str,
    placeholders: Mapping[PlaceholderKey, int | Iterable[int]] | None = None,
    *,
    dirty: Iterable[PlaceholderKey] = (),
) -> str:
    """Insert redundant color codes so the entry emoji never lands on bold text.

    Hypixel splits every scoreboard line at 16 characters and wedges a
    blank-glyph emoji into the seam. The renderer advances an extra pixel for
    each bold character, so an emoji that inherits bold opens a visible hole
    between two letters. This returns an equivalent line -- identical visible
    text and styling -- whose seam always falls on a color code.

    ``placeholders`` declares, per placeholder, every rendered length it may
    take; the result is checked against all combinations of them. Rendered
    means what Housing prints, including thousands separators, so use
    :func:`number_lengths` for numeric variables. Only placeholders that can
    resolve early enough to move the seam need declaring -- one that starts
    past it is counted as :data:`ASSUMED_LENGTH` for the truncation estimate
    alone, which makes that estimate a lower bound. Placeholders in ``dirty`` may
    themselves resolve to color codes: the styling behind them is unknowable,
    so the seam is only ever allowed to land somewhere the codes have since
    been reasserted.
    """
    declared, dirty_strings = _collect(placeholders, dirty)
    template, mapping = _normalize(text)
    spans = _placeholder_spans(template)

    missing = _reaching_the_seam(template, spans, declared)
    if missing:
        raise ValueError(
            'no lengths declared for placeholder(s) '
            + ', '.join(repr(token) for token in missing)
            + ' -- they resolve early enough to move the seam, so pass them '
            'in `placeholders`',
        )

    per_placeholder = [
        declared.get(template[start:end], (ASSUMED_LENGTH,)) for start, end in spans
    ]
    total = 1
    for lengths in per_placeholder:
        total *= len(lengths)
    if total > MAX_COMBINATIONS:
        raise ValueError(
            f'{total} placeholder length combinations exceeds the '
            f'{MAX_COMBINATIONS} checked; declare fewer lengths',
        )

    dirty_flags = tuple(template[start:end] in dirty_strings for start, end in spans)
    combinations = tuple(itertools.product(*per_placeholder))
    baseline = tuple(
        _render(_resolve(template, spans, lengths, dirty_flags))
        for lengths in combinations
    )
    problem = _Problem(template, spans, dirty_flags, combinations, baseline)

    if problem.check(()):
        _warn_dropped(text, problem, ())
        _warn_length(text)
        return text

    budget = MAX_INSERTED_LENGTH
    points = _insertion_points(template, spans)
    states = _states(template)
    for insertions in _candidates(points, states, budget):
        if not problem.check(insertions):
            continue
        _warn_dropped(text, problem, insertions)
        result = _splice(
            text,
            tuple(
                (mapping[point], payload.replace('§', '&'))
                for point, payload in insertions
            ),
        )
        _warn_length(result)
        return result

    raise ValueError(
        f'cannot keep the seam off bold text by inserting at most '
        f'{MAX_INSERTED_LENGTH} characters: {text!r}'
        + (
            ' -- a placeholder straddles the seam for at least one of its '
            'declared lengths, so shorten the text before it or declare '
            'fewer lengths'
            if spans
            else ''
        ),
    )


def _warn_length(text: str) -> None:
    if len(text) <= KNOWN_GOOD_SOURCE_LENGTH:
        return
    warn(
        f'{text!r} is {len(text)} characters of source; lines up to '
        f'{KNOWN_GOOD_SOURCE_LENGTH} are known to be accepted in game and '
        f'longer ones are untested, so check it is not truncated',
    )


def _warn_dropped(
    text: str,
    problem: _Problem,
    insertions: tuple[tuple[int, str], ...],
) -> None:
    dropped = problem.worst_dropped(insertions)
    if not dropped:
        return
    warn(
        f'{dropped} character(s) of {text!r} are cut off in game: a line '
        f'renders as two {FIELD_MAX_LENGTH}-character fields, and the codes '
        f'Hypixel reapplies after the seam are charged to the second one',
    )


def _digit_counts(low: int, high: int) -> set[int]:
    if low > high:
        return set()
    return set(range(len(str(low)), len(str(high)) + 1))


def number_lengths(
    low: int,
    high: int,
    *,
    decimals: int = 0,
    group: bool = True,
) -> tuple[int, ...]:
    """Rendered lengths of every number in ``[low, high]``.

    Housing groups thousands, so 1234 prints as ``1,234`` and occupies five
    characters, not four.
    """
    if low > high:
        raise ValueError(f'empty range: {low} > {high}')
    if decimals < 0:
        raise ValueError(f'negative decimals: {decimals}')

    lengths: set[int] = set()
    fraction = decimals + 1 if decimals else 0
    magnitudes = (
        (_digit_counts(max(low, 0), high), 0),
        (_digit_counts(max(-high, 1), -low), 1),
    )
    for digits, sign in magnitudes:
        for count in digits:
            grouped = (count - 1) // 3 if group else 0
            lengths.add(count + grouped + fraction + sign)
    return tuple(sorted(lengths))
