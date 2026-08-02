from pyhtsw import (
    Container,
    DamageAmount,
    HasPermission,
    IfAll,
    PlayerHealth,
    PlayerHunger,
    PlayerMaxHealth,
    PlayerStat,
    PlayerTime,
    PortalType,
    chat,
    set_player_time,
    set_player_weather,
    toggle_nametag_display,
)

with Container() as container:
    set_player_weather('Sunny')
    set_player_time(PlayerTime.NOON)
    set_player_time(1000)
    toggle_nametag_display(False)
    toggle_nametag_display(True)

assert container.into_htsl() == (
    'playerWeather "Sunny"\n'
    'playerTime 6000\n'
    'playerTime 1000\n'
    'displayNametag false\n'
    'displayNametag true'
), container.into_htsl()


assert PlayerTime.SUNRISE == 0
assert PlayerTime.NOON == 6000
assert PlayerTime.SUNSET == 12000
assert PlayerTime.MIDNIGHT == 18000


# htsw bounds playerTime to 0-23999 and types it as a plain number.
for bad in (-1, 24000):
    raised = False
    with Container():
        try:
            set_player_time(bad)
        except ValueError:
            raised = True
    assert raised, f'expected a ValueError for playerTime {bad}'

raised = False
with Container():
    try:
        set_player_time(PlayerStat('x'))  # type: ignore[arg-type]
    except TypeError:
        raised = True
assert raised, 'expected a TypeError for a stat playerTime'


with Container() as conditions:
    with IfAll(
        HasPermission('Fly'),
        HasPermission('Item: Mailbox'),
        PortalType('Nether Portal'),
        PortalType('End Portal'),
        DamageAmount > 5,
        ~(DamageAmount == 0),
    ):
        chat('ok')

assert conditions.into_htsl() == (
    'if and (hasPermission "Fly", hasPermission "Item: Mailbox", '
    'portal Nether_Portal, portal End_Portal, '
    'damageAmount > 5, !damageAmount == 0) {\n'
    '    chat "ok"\n'
    '}'
), conditions.into_htsl()


# `health`, not `changeHealth`, and no trailing fallback on any of the three.
with Container() as vitals:
    with IfAll(PlayerHealth > 3, PlayerMaxHealth >= 20, PlayerHunger < 4):
        chat('ok')

assert vitals.into_htsl() == (
    'if and (health > 3.0, maxHealth >= 20.0, hunger < 4) {\n    chat "ok"\n}'
), vitals.into_htsl()


# A var comparison still carries its fallback.
with Container() as var_fallback:
    with IfAll(PlayerStat('kills', fallback_value=7) > 3):
        chat('ok')

assert var_fallback.into_htsl() == ('if and (var "kills" > 3 7) {\n    chat "ok"\n}'), (
    var_fallback.into_htsl()
)
