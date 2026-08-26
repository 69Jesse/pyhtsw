from pyhtsw import Container, ExecutionContext, PlayerStat, Preserved
from pyhtsw.expression.binary_expression import BinaryExpression


def overwritten_store_count(protect: bool) -> int:
    with Container() as container:
        stat = PlayerStat('pv0').as_long()
        if protect:
            with Preserved():
                stat.value = 111
                stat.value = 222
        else:
            stat.value = 111
            stat.value = 222
    return container.expression_counts(nested=True).get(BinaryExpression, 0)


# Control: without Preserved() the overwritten store is dead and removed.
assert overwritten_store_count(protect=False) == 1
assert overwritten_store_count(protect=True) == 2


# The no-op, fold and identity-merge passes also leave the region alone.
with Container() as container:
    stat = PlayerStat('pv1').as_long()
    with Preserved():
        stat.value = 0
        stat.value += 5
        stat.value += 0
        stat.value *= 1
counts = container.expression_counts(nested=True)
assert counts.get(BinaryExpression, 0) == 4, counts

with Container() as container:
    stat = PlayerStat('pv1').as_long()
    stat.value = 0
    stat.value += 5
    stat.value += 0
    stat.value *= 1
counts = container.expression_counts(nested=True)
assert counts.get(BinaryExpression, 0) == 1, counts


# Preserved expressions still execute normally.
with ExecutionContext() as ctx:
    stat = PlayerStat('pv2').as_long()
    with Preserved():
        stat.value = 40
        stat.value += 2

    def check() -> None:
        assert int(ctx.get(stat)) == 42

    ctx.assert_all(check)
