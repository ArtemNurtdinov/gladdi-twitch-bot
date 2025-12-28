from dataclasses import dataclass
from datetime import datetime

from app.twitch.application.interaction.dto import ChatContextDTO


@dataclass(frozen=True)
class BalanceDTO:
    channel_name: str
    display_name: str
    user_name: str
    bot_nick: str
    occurred_at: datetime


@dataclass(frozen=True)
class BonusDTO(ChatContextDTO):
    pass
