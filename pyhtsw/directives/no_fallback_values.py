from pyhtsw.directives.base import Directive

__all__ = ('NoFallbackValues',)


class NoFallbackValues(Directive):
    pass


def no_fallback_values() -> bool:
    return NoFallbackValues.active()
