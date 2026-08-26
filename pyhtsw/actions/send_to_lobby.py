from typing import Self, final

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.registry import ActionMeta

from ..expression.expression import Expression

__all__ = (
    'SendToLobbyExpression',
    'send_to_lobby',
)


@final
class SendToLobbyExpression(Expression):
    htsw_meta = ActionMeta(
        htsw_name='SEND_TO_LOBBY',
        limit=1,
        control=True,
        display_name='Send to Lobby',
        forbidden_in_events=True,
    )

    lobby: str

    def __init__(self, lobby: str) -> None:
        self.lobby = lobby

    def into_htsl(self) -> str:
        return f'lobby {self.inline_quoted(self.lobby)}'

    def cloned(
        self,
        *,
        lobby: str | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'lobby': lobby,
            },
        )


def send_to_lobby(lobby: str) -> None:
    SendToLobbyExpression(lobby=lobby).write()
