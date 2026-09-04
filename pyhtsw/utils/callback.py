import inspect
from collections.abc import Callable
from typing import Any

__all__ = ('call_with_optional_args',)

_POSITIONAL = (
    inspect.Parameter.POSITIONAL_ONLY,
    inspect.Parameter.POSITIONAL_OR_KEYWORD,
)


def _required_arg_count(callback: Callable[..., Any], noun: str) -> int | None:
    try:
        parameters = inspect.signature(callback).parameters
    except (TypeError, ValueError) as error:
        raise TypeError(
            f'Unable to inspect the signature of {noun} {callback!r}. '
            f'Wrap it in a lambda that takes the arguments you want.',
        ) from error
    required = 0
    for parameter in parameters.values():
        if parameter.kind is inspect.Parameter.VAR_POSITIONAL:
            return None
        if (
            parameter.kind in _POSITIONAL
            and parameter.default is inspect.Parameter.empty
        ):
            required += 1
    return required


def call_with_optional_args[T](
    callback: Callable[..., T],
    *args: Any,
    noun: str = 'callable',
) -> T:
    required = _required_arg_count(callback, noun)
    if required is None:
        return callback(*args)
    if required > len(args):
        raise ValueError(
            f'Callable {noun} must take at most {len(args)} required arguments, got {required}',
        )
    return callback(*args[:required])
