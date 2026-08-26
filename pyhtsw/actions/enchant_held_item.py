from typing import Self, final

from pyhtsw.actions.enchantment import Enchantment
from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.expression.expression import Expression
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Resource
from pyhtsw.types import ALL_ENCHANTMENTS

__all__ = (
    'EnchantHeldItemExpression',
    'enchant_held_item',
)


@final
class EnchantHeldItemExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='ENCHANT_HELD_ITEM',
        limit=24,
        effects=Effects.of(reads=(Resource.INVENTORY,), writes=(Resource.INVENTORY,)),
        display_name='Enchant Held Item',
        forbidden_events=('Player Quit',),
    )

    enchantment_name: str
    level: int

    def __init__(self, enchantment_name: str, level: int) -> None:
        self.enchantment_name = enchantment_name
        self.level = level

    def into_htsl(self) -> str:
        return f'enchant {self.inline_quoted(self.enchantment_name)} {self.inline(self.level)}'

    def cloned(
        self,
        *,
        enchantment_name: str | Missing = MISSING,
        level: int | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'enchantment_name': enchantment_name,
                'level': level,
            },
        )


def enchant_held_item(
    enchantment: ALL_ENCHANTMENTS | Enchantment,
    level: int | None = None,
) -> None:
    if isinstance(enchantment, Enchantment):
        name = enchantment.name
        if level is None:
            level = enchantment.level
    else:
        name = enchantment
    if level is None:
        level = 1
    EnchantHeldItemExpression(enchantment_name=name, level=level).write()
