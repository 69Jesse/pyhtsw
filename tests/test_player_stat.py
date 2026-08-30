from pyhtsw import Container, PlayerStat
from pyhtsw.stats.stat import StatNameError

with Container() as container:
    x = PlayerStat('x')
    x.value = 5

assert container.into_htsl() == 'var "x" = 5 true', container.into_htsl()


# htsw's parseVarName rejects a space, an empty name and anything over 16
# characters; all three are caught where the stat is constructed.
for bad in ('with space', '', 'seventeen_chars_x'):
    try:
        PlayerStat(bad)
    except StatNameError:
        pass
    else:
        raise AssertionError(f'PlayerStat({bad!r}) should have been rejected')


assert PlayerStat('sixteen_chars_xx').name == 'sixteen_chars_xx'
