from pyhtsw import (
    Container,
    Location,
    PlayerStat,
    TemporaryStat,
    teleport_player,
)

# A plain stat, a held temp and a computed expression all drop the fallback
with Container() as container:
    x = PlayerStat('x').as_double()
    held = TemporaryStat().as_double()
    held.value = x + 1
    teleport_player(Location.custom(x, 106.0, -119.5))
    teleport_player(Location.custom(held, 106.0, -119.5))
    teleport_player(Location.custom(x + 1, 106.0, -119.5))

assert container.into_htsl() == (
    'var "tmp0" = "%var.player/x 0.0%D" false\n'
    'var "tmp0" += 1.0 false\n'
    'tp "custom_coordinates" "%var.player/x% 106.0 -119.5" false\n'
    'tp "custom_coordinates" "%var.player/tmp0% 106.0 -119.5" false\n'
    'var "tmp1" = "%var.player/x 0.0%D" false\n'
    'var "tmp1" += 1.0 false\n'
    'tp "custom_coordinates" "%var.player/tmp1% 106.0 -119.5" false'
), container.into_htsl()


# Pitch and yaw go through the same join, so they drop it too
with Container() as container:
    pitch = PlayerStat('pitch').as_double()
    teleport_player(Location.custom(1, 2, 3, pitch, 90.0))

assert container.into_htsl() == (
    'tp "custom_coordinates" "1 2 3 %var.player/pitch% 90.0" false'
), container.into_htsl()
