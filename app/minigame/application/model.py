from dataclasses import dataclass
from datetime import datetime

from app.commands.dto import ChatContextDTO


@dataclass(frozen=True)
class MinigameTickDTO:
    channel_name: str
    occurred_at: datetime


@dataclass(frozen=True)
class RpsDTO(ChatContextDTO):
    command_prefix: str
    command_name: str
    choice_input: str | None
