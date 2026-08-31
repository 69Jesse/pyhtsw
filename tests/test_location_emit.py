from pyhtsw import (
    Container,
    Item,
    Location,
    PlayerStat,
    drop_item,
    launch_to_target,
    play_sound,
    set_compass_target,
    teleport_player,
)
from pyhtsw.stats.stat import Stat

# The keyword htsw's parser accepts, not the one that reads nicely: upstream
# names it "House Spawn Location".
assert Location.house_spawn().into_htsl() == '"house_spawn_location"'
assert Location.invokers().into_htsl() == '"invokers_location"'
assert Location.current().into_htsl() == '"current_location"'
assert Location.custom(1, 2, 3).into_htsl() == '"custom_coordinates" "1 2 3"'
assert Location.custom(1, 2, 3, 4, 5).into_htsl() == '"custom_coordinates" "1 2 3 4 5"'


# Every action that takes one, with and without coordinates.
with Container() as container:
    teleport_player(Location.invokers())
    launch_to_target(Location.house_spawn(), strength=3)
    set_compass_target(Location.current())
    play_sound('note.pling')
    drop_item(Item('stick'), Location.invokers())

assert container.into_htsl() == (
    'tp "invokers_location" false\n'
    'launchTarget "house_spawn_location" 3\n'
    'compassTarget "current_location"\n'
    'sound "note.pling" 0.7 1.0 "invokers_location"\n'
    'dropItem "Stick" "invokers_location" false false false false 6000 10'
), container.into_htsl()


with Container() as container:
    teleport_player(Location.custom(1, 2, 3))
    launch_to_target(Location.custom(1, 2, 3), strength=3)
    set_compass_target(Location.custom(1, 2, 3))
    play_sound('note.pling', location=Location.custom(1, 2, 3))
    drop_item(Item('stick'), Location.custom(1, 2, 3))

assert container.into_htsl() == (
    'tp "custom_coordinates" "1 2 3" false\n'
    'launchTarget "custom_coordinates" "1 2 3" 3\n'
    'compassTarget "custom_coordinates" "1 2 3"\n'
    'sound "note.pling" 0.7 1.0 "custom_coordinates" "1 2 3"\n'
    'dropItem "Stick" "custom_coordinates" "1 2 3" false false false false 6000 10'
), container.into_htsl()


# The coordinate string is derived, never stored: mutating an operand has to
# show up in the render, and rendering twice must not register a second deferred
# computation (which is what a stored string was hiding).
location = Location.custom(1, 2, 3)
location.x = 99
location.yaw = 45.0
assert location.into_htsl() == '"custom_coordinates" "99 2 3 45.0 0"', (
    location.into_htsl()
)

repeated = Location.custom(PlayerStat('a').as_double(), 2, 3)
assert (
    repeated.into_htsl()
    == repeated.into_htsl()
    == ('"custom_coordinates" "%var.player/a% 2 3"')
), repeated.into_htsl()


# A computed operand is replaced by the temp the resolver materialised, so the
# render follows the substitution rather than needing its text rewritten.
with Container() as container:
    x = PlayerStat('x').as_double()
    computed = Location.custom(x + 1, 2, 3)
    teleport_player(computed)

assert container.into_htsl() == (
    'var "tmp0" = "%var.player/x 0.0%D" false\n'
    'var "tmp0" += 1.0 false\n'
    'tp "custom_coordinates" "%var.player/tmp0% 2 3" false'
), container.into_htsl()
assert isinstance(computed.x, Stat), computed.x
assert computed.x.name == 'tmp0', computed.x
