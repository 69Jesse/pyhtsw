import re
from typing import final

from pyhtsw.compiler.registry import ActionMeta
from pyhtsw.compiler.schedule import Effects
from pyhtsw.execute.backend_type import BackendType, JavaLong
from pyhtsw.internal_type import InternalType
from pyhtsw.placeholders.base import PlaceholderCheckable

__all__ = (
    'HouseCookiesPlaceholder',
    'HouseCookies',
    'HouseGuestsPlaceholder',
    'HouseGuests',
    'HousePlayersPlaceholder',
    'HousePlayers',
    'HouseVisitingRulesPlaceholder',
    'HouseVisitingRules',
)


@final
class HouseCookiesPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%house.cookies%')),
    pattern_factory=lambda _: HouseCookies,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%house.cookies%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(0)


HouseCookies = HouseCookiesPlaceholder()


@final
class HouseGuestsPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%house.guests%')),
    pattern_factory=lambda _: HouseGuests,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%house.guests%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(0)


HouseGuests = HouseGuestsPlaceholder()


@final
class HousePlayersPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%house.players%')),
    pattern_factory=lambda _: HousePlayers,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%house.players%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return JavaLong(0)


HousePlayers = HousePlayersPlaceholder()


@final
class HouseVisitingRulesPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%house.visitingrules%')),
    pattern_factory=lambda _: HouseVisitingRules,
):
    htsw_meta = ActionMeta(
        effects=Effects.of(),
    )

    def __init__(self) -> None:
        super().__init__(
            placeholder='%house.visitingrules%',
            constant_internal_type=InternalType.STRING,
        )

    def get_backend_value(self) -> BackendType:
        return ''


HouseVisitingRules = HouseVisitingRulesPlaceholder()
