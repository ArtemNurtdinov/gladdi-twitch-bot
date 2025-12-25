from dataclasses import dataclass

from app.twitch.application.dto import ChatContextDTO


@dataclass(frozen=True)
class TopDTO(ChatContextDTO):
    limit: int


@dataclass(frozen=True)
class BottomDTO(ChatContextDTO):
    limit: int

