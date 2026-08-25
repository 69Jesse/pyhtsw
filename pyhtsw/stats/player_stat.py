import re
from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.expression.housing_type import HousingType, housing_type_from_string
from pyhtsw.internal_type import InternalType

from .stat import Stat

__all__ = ('PlayerStat',)


def _split_parts(value: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    in_quotes = False
    for char in value:
        if char == '"':
            in_quotes = not in_quotes
        elif char == ' ' and not in_quotes:
            if current:
                parts.append(''.join(current))
                current.clear()
        else:
            current.append(char)
    if current:
        parts.append(''.join(current))
    return parts


def _player_stat_factory(match: re.Match[str]) -> 'PlayerStat':
    parts = _split_parts(match.group(1))
    name = parts[0] if len(parts) > 0 else ''
    stat = PlayerStat(name)
    if len(parts) > 1:
        stat = stat.with_fallback(housing_type_from_string(parts[1]))
    return stat


@final
class PlayerStat(
    Stat,
    pattern=re.compile(r'%var\.player/([^%]+)%'),
    pattern_factory=_player_stat_factory,
):
    @staticmethod
    def left_side_keyword() -> str:
        return 'var'

    @staticmethod
    def right_side_keyword() -> str:
        return 'player'

    def is_execution_player_scoped(self) -> bool:
        return True

    def cloned(
        self,
        *,
        name: str | Missing = MISSING,
        internal_type: InternalType | Missing = MISSING,
        fallback_value: HousingType | None | Missing = MISSING,
        auto_unset: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'name': name,
                'internal_type': internal_type,
                'fallback_value': fallback_value,
                'auto_unset': auto_unset,
            },
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.name} {self.internal_type.name}>'
