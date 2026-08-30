__all__ = ('check_bounds',)


def check_bounds[T](value: T, *, field: str, minimum: float, maximum: float) -> T:
    """Reject a literal outside Housing's range for `field`. A non-literal
    (a `Checkable`) is only known at runtime, so it passes through."""
    if not isinstance(value, int | float) or isinstance(value, bool):
        return value
    if value < minimum or value > maximum:
        raise ValueError(
            f'{field} is {value}, outside the allowed range {minimum}-{maximum}.',
        )
    return value
