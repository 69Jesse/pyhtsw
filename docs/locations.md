# Locations

Several actions take a `Location`. Construct one via the factory classmethods —
the bare `Location` class is **not** a valid value.

```python
from pyhtsw import Location

Location.custom(10, 65, 10)                  # x, y, z
Location.custom(10, 65, 10, 90, 0)           # x, y, z, yaw, pitch
Location.custom(10, 65, 10, pitch=0, yaw=90) # the same, by name
Location.house_spawn()
Location.invokers()
Location.current()
```

Used by actions such as `teleport_player`, `drop_item`, `play_sound`,
`set_compass_target`, and `launch_to_target`:

```python
from pyhtsw import teleport_player, Location

teleport_player(Location.house_spawn())
teleport_player(Location.custom(10, 65, 10, yaw=180))
```

Coordinates accept numbers or stat/expression values.

Rotation is written **yaw first**, `x y z yaw pitch`, which is the order htsw's
coordinate parser reads and the order a house built in-game stores. htsw's
prose action reference says pitch first; it is wrong, and following it points
players the wrong way.
