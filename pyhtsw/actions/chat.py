from typing import TYPE_CHECKING, Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.expression.expression import Expression
from pyhtsw.registry import ActionMeta
from pyhtsw.schedule import Effects, Stream
from pyhtsw.utils.formatting import formatting_to_ansi
from pyhtsw.utils.log import log

if TYPE_CHECKING:
    from pyhtsw.execute.context import ExecutionContext


__all__ = (
    'ChatExpression',
    'chat',
)


@final
class ChatExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='MESSAGE',
        limit=20,
        effects=Effects.of(stream=Stream.TEXT),
        display_name='Send a Chat Message',
        forbidden_events=('Player Quit',),
    )

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
