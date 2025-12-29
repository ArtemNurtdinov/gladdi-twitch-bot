from dataclasses import dataclass

from app.twitch.application.interaction.dto import ChatContextDTO


@dataclass(frozen=True)
class ChatMessageDTO(ChatContextDTO):
    message: str
