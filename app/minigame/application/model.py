from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.commands.dto import ChatContextDTO


@dataclass(frozen=True)
class MinigameTickDTO:
    channel_name: str
    occurred_at: datetime

@dataclass(frozen=True)
class RpsDTO(ChatContextDTO):
    choice_input: Optional[str]