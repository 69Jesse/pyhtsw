from typing import Any, ClassVar, Self

__all__ = ('Directive',)


class Directive:
    """A context-manager flag scoped to the block it wraps. Each subclass gets
    its own stack, so nesting works and `active()` answers for the innermost
    open block of that kind."""

    _stack: ClassVar[list[Any]]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls._stack = []

    def __enter__(self) -> Self:
        type(self)._stack.append(self)
        return self

    def __exit__(self, *args: object) -> None:
        type(self)._stack.pop()

    @classmethod
    def active(cls) -> bool:
        return bool(cls._stack)
