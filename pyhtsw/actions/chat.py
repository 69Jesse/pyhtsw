from typing import TYPE_CHECKING, Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.utils.formatting import formatting_to_ansi
from pyhtsw.utils.log import log

from ..expression.expression import Expression

if TYPE_CHECKING:
    from ..execute.context import ExecutionContext


__all__ = (
    'ChatExpression',
    'chat',
)


@final
class ChatExpression(Expression):
    line: str

    def __init__(self, line: str) -> None:
        self.line = line

    def into_htsl(self) -> str:
        return f'chat {self.inline_quoted(self.line)}'

    def raw_execute(self, context: 'ExecutionContext') -> None:
        log(
            formatting_to_ansi(
                f'&7* &f{context.get(self.line, cast=False, output="string")}',
            ),
        )

    def cloned(
        self,
        *,
        line: str | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'line': line,
            },
        )


def chat(line: str) -> None:
    ChatExpression(line=line).write()
