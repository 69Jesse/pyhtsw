from collections.abc import Sequence

from pyhtsw.checkable import Checkable
from pyhtsw.editable import Editable
from pyhtsw.ext.approximate import approximate_sin_cos
from pyhtsw.placeholders.player import PlayerPositionPitch, PlayerPositionYaw
from pyhtsw.stats.temporary_stat import TemporaryStat

__all__ = ('DIRECTION_SCALE', 'approximate_look_vector', 'emit_direction_squared')

# A unit vector's components round-trip through three decimals, so |v|^2 lands
# at ~1 with 5e-4 of relative error - which a projection identity multiplies by
# the squared distance. Squaring pre-scaled keeps that relative error at ~1e-9.
DIRECTION_SCALE = 1_000_000.0


def emit_direction_squared(
    destination: Editable,
    scratch: Editable,
    components: Sequence[Checkable],
) -> None:
    """destination <- |components|^2 * DIRECTION_SCALE."""
    first, *rest = components
    destination.value = first
    destination.value *= DIRECTION_SCALE
    destination.value *= first
    for component in rest:
        scratch.value = component
        scratch.value *= DIRECTION_SCALE
        scratch.value *= component
        destination.value += scratch


def approximate_look_vector(
    *,
    assign_to_x: Editable,
    assign_to_y: Editable,
    assign_to_z: Editable,
    yaw: Checkable = PlayerPositionYaw,
    pitch: Checkable = PlayerPositionPitch,
) -> None:
    """Write the unit look vector for `yaw`/`pitch` into the three stats.

    Minecraft convention:
        x = -sin(yaw)·cos(pitch),  y = -sin(pitch),  z = cos(yaw)·cos(pitch)

    `yaw`/`pitch` default to the executing player's, and are assumed to be in
    Minecraft's ranges ([-180, 180] and [-90, 90]). `assign_to_*` may be any
    editable stats — global, player, temporary — making this reusable for look
    rays, dash/velocity vectors, knockback directions, and so on.
    """
    approximate_sin_cos(
        yaw,
        assign_to_sin=assign_to_x,
        assign_to_cos=assign_to_z,
        certain_x_in_range=180,
        sin_sign=-1,
    )
    xz_multiplier = TemporaryStat().as_double()
    approximate_sin_cos(
        pitch,
        assign_to_sin=assign_to_y,
        assign_to_cos=xz_multiplier,
        certain_x_in_range=90,
        sin_sign=-1,
    )
    assign_to_x.value *= xz_multiplier
    assign_to_z.value *= xz_multiplier
