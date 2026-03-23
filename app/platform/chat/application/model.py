from dataclasses import dataclass

from app.commands.dto import ChatContextDTO


@dataclass(frozen=True)
class ChatMessageDTO(ChatContextDTO):
    message: str
