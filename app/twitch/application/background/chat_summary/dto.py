from dataclasses import dataclass

from app.twitch.application.interaction.dto import ChatContextDTO


@dataclass(frozen=True)
class ChatSummarizerDTO(ChatContextDTO):
    interval_minutes: int

