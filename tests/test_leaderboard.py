import io
from contextlib import redirect_stdout

from helpers import expect_exception

from pyhtsw import Container, EmulatedHouse, GlobalStat, PlayerStat
from pyhtsw.expression.condition.conditional_expression import ConditionalExpression
from pyhtsw.ext.leaderboard import KEY_LIMIT, SortedTopN

CAPACITY = 5
EMPTY = ('---', '--:--', 0)


def build(capacity: int = CAPACITY, **kwargs: object) -> SortedTopN:
    return SortedTopN(
        slots=[
            (
                GlobalStat(f'ln{i}').as_string(),
                GlobalStat(f'lt{i}').as_string(),
                GlobalStat(f'lf{i}').as_long(),
                GlobalStat(f'lk{i}').as_long(),
            )
            for i in range(capacity)
        ],
        key_column=-1,
        identity_column=0,
        empty=(*EMPTY, 0),
        **kwargs,  # type: ignore[arg-type]
    )


def names_of(board: SortedTopN, house: EmulatedHouse) -> list[str]:
    return [str(house.get_raw(slot[0])) for slot in board.slots]


def keys_of(board: SortedTopN, house: EmulatedHouse) -> list[int]:
    return [int(house.get_raw(slot[3])) for slot in board.slots]


# === Ordering ===

# Entries land in ascending key order regardless of insertion order.
with EmulatedHouse(ignore_action_limits=True) as house:
    board = build()
    board.seed()
    for name, ms in (('c', 3000), ('a', 1000), ('d', 4000), ('b', 2000)):
        board.insert((name, f'{ms}ms', 0, ms))

    def check_sorted(_b: SortedTopN = board) -> None:
        assert names_of(_b, house) == ['a', 'b', 'c', 'd', '---']
        assert keys_of(_b, house)[:4] == [1000, 2000, 3000, 4000]

    house.assert_all(check_sorted)


# A full board evicts the worst entry, and a row that misses changes nothing.
with EmulatedHouse(ignore_action_limits=True) as house:
    board = build()
    board.seed()
    for i, ms in enumerate((1000, 2000, 3000, 4000, 5000)):
        board.insert((chr(ord('a') + i), 't', 0, ms))
    board.insert(('mid', 't', 0, 2500))
    board.insert(('slow', 't', 0, 9000))

    def check_evicted(_b: SortedTopN = board) -> None:
        assert names_of(_b, house) == ['a', 'b', 'mid', 'c', 'd']

    house.assert_all(check_evicted)


# Ties keep the older entry ahead of the newer one.
with EmulatedHouse(ignore_action_limits=True) as house:
    board = build()
    board.seed()
    board.insert(('first', 't', 0, 500))
    board.insert(('second', 't', 0, 500))

    def check_tie(_b: SortedTopN = board) -> None:
        assert names_of(_b, house)[:2] == ['first', 'second']

    house.assert_all(check_tie)


# All four columns travel together when a row shifts.
with EmulatedHouse(ignore_action_limits=True) as house:
    board = build()
    board.seed()
    board.insert(('slowpoke', '9.99', 7, 9000))
    board.insert(('speedy', '1.11', 2, 1000))

    def check_columns(_b: SortedTopN = board) -> None:
        assert str(house.get_raw(_b.slots[0][1])) == '1.11'
        assert int(house.get_raw(_b.slots[0][2])) == 2
        assert str(house.get_raw(_b.slots[1][1])) == '9.99'
        assert int(house.get_raw(_b.slots[1][2])) == 7

    house.assert_all(check_columns)


# === Identity / dedupe ===

# A better time replaces the player's own row instead of adding a second one.
with EmulatedHouse(ignore_action_limits=True) as house:
    board = build()
    board.seed()
    board.insert(('bob', 't', 0, 5000), identity='bob')
    board.insert(('amy', 't', 0, 3000), identity='amy')
    board.insert(('bob', 't', 0, 1000), identity='bob')

    def check_dedupe(_b: SortedTopN = board) -> None:
        assert names_of(_b, house) == ['bob', 'amy', '---', '---', '---']
        assert keys_of(_b, house)[:2] == [1000, 3000]

    house.assert_all(check_dedupe)


# A worse time from a player already on the board is ignored entirely.
with EmulatedHouse(ignore_action_limits=True) as house:
    board = build()
    board.seed()
    board.insert(('bob', 'good', 1, 1000), identity='bob')
    board.insert(('amy', 't', 0, 3000), identity='amy')
    board.insert(('bob', 'bad', 9, 8000), identity='bob')

    def check_ignored(_b: SortedTopN = board) -> None:
        assert names_of(_b, house)[:2] == ['bob', 'amy']
        assert keys_of(_b, house)[0] == 1000
        assert str(house.get_raw(_b.slots[0][1])) == 'good'
        assert int(house.get_raw(_b.slots[0][2])) == 1

    house.assert_all(check_ignored)


# Improving inside a full board keeps every other row, and nothing is evicted.
with EmulatedHouse(ignore_action_limits=True) as house:
    board = build()
    board.seed()
    for i, ms in enumerate((1000, 2000, 3000, 4000, 5000)):
        board.insert((chr(ord('a') + i), 't', 0, ms), identity=chr(ord('a') + i))
    board.insert(('e', 't', 0, 1500), identity='e')

    def check_full_improve(_b: SortedTopN = board) -> None:
        assert names_of(_b, house) == ['a', 'e', 'b', 'c', 'd']

    house.assert_all(check_full_improve)


# Without an identity the same player can hold several rows.
with EmulatedHouse(ignore_action_limits=True) as house:
    board = build()
    board.seed()
    board.insert(('bob', 't', 0, 5000))
    board.insert(('bob', 't', 0, 1000))

    def check_no_identity(_b: SortedTopN = board) -> None:
        assert names_of(_b, house)[:2] == ['bob', 'bob']

    house.assert_all(check_no_identity)


# === Descending ===

# order='descending' ranks the highest key first.
with EmulatedHouse(ignore_action_limits=True) as house:
    board = build(order='descending')
    board.seed()
    for name, score in (('low', 10), ('high', 900), ('mid', 400)):
        board.insert((name, 't', 0, score))

    def check_descending(_b: SortedTopN = board) -> None:
        assert names_of(_b, house)[:3] == ['high', 'mid', 'low']

    house.assert_all(check_descending)


# === Callbacks ===

# if_entered fires only for a row that made the board; if_missed for one that did not.
buffer = io.StringIO()
with redirect_stdout(buffer), EmulatedHouse(ignore_action_limits=True) as house:
    board = build()
    board.seed()
    for i, ms in enumerate((1000, 2000, 3000, 4000, 5000)):
        board.insert((chr(ord('a') + i), 't', 0, ms))
    board.insert(
        ('nope', 't', 0, 9999),
        if_entered=lambda: house.print('entered'),
        if_missed=lambda: house.print('missed'),
    )
    board.insert(
        ('yes', 't', 0, 1),
        if_entered=lambda: house.print('entered'),
        if_missed=lambda: house.print('missed'),
    )
printed = buffer.getvalue().split()
assert printed == ['missed', 'entered'], printed


# === Seeding ===

# A board that was never seeded reads unset keys as 0, which outrank everything.
with EmulatedHouse(ignore_action_limits=True) as house:
    board = build()
    board.insert(('real', 't', 0, 1000))

    def check_unseeded(_b: SortedTopN = board) -> None:
        assert names_of(_b, house)[0] != 'real'

    house.assert_all(check_unseeded)


# === Validation ===

with expect_exception(ValueError):
    SortedTopN(slots=[])

# A STRING key column has no usable ordering.
with expect_exception(ValueError):
    SortedTopN(slots=[(GlobalStat('x0').as_string(),), (GlobalStat('x1').as_string(),)])

with expect_exception(ValueError):
    SortedTopN(slots=[(GlobalStat('y').as_long(),), (GlobalStat('y').as_long(),)])

# A key at the sentinel would overflow the sign-bit rank count.
with expect_exception(ValueError):
    build().insert(('a', 'b', 0, KEY_LIMIT))

with expect_exception(ValueError):
    SortedTopN(slots=[(GlobalStat(f'z{i}').as_long(),) for i in range(3)]).insert(
        0,
        identity='bob',
    )

with expect_exception(ValueError):
    build().insert(('a', 'b', 0))


# === Cost ===
#
# Measured behind a full action list so the limit fixer realizes the wrappers
# it would add - the canonical worst-case-conditional metric.
def measure(*, identity: bool) -> int:
    with Container(ignore_action_limits=True) as container:
        for _ in range(25):
            PlayerStat('fill1').value += PlayerStat('fill2')
        board = build()
        board.insert(
            ('n', 't', 0, PlayerStat('ms').as_long()),
            identity='n' if identity else None,
        )
    return container.expression_counts()[ConditionalExpression]


plain = measure(identity=False)
deduped = measure(identity=True)
assert plain <= 12, plain
assert deduped <= 20, deduped
