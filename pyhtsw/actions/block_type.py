from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with

from ..expression.condition.condition import Condition
from .item import Item, item_action_reference, item_referenced_importables

__all__ = ('BlockType',)


@final
class BlockType(Condition):
    block: Item
    match_type_only: bool

    def __init__(
        self,
        block: Item,
        match_type_only: bool = False,
    ) -> None:
        self.block = block
        self.match_type_only = match_type_only

    def into_htsl_raw(self) -> str:
        name = item_action_reference(self.block)
        return (
            f'blockType {self.inline_quoted(name)} {self.inline(self.match_type_only)}'
        )

    def referenced_importables(self) -> list[tuple[str, str]]:
        return item_referenced_importables(self.block)

    def cloned(
        self,
        *,
        block: Item | Missing = MISSING,
        match_type_only: bool | Missing = MISSING,
        inverted: bool | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'block': block,
                'match_type_only': match_type_only,
                'inverted': inverted,
            },
        )
