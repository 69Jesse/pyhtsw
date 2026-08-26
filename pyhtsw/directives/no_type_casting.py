from pyhtsw.directives.base import Directive

__all__ = ('NoTypeCasting',)


class NoTypeCasting(Directive):
    pass


def no_type_casting() -> bool:
    return NoTypeCasting.active()
