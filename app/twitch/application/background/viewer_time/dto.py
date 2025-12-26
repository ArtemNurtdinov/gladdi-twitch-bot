from dataclasses import dataclass
from datetime import datetime

from app.twitch.application.interaction.dto import ChatContextDTO


@dataclass(frozen=True)
class ViewerTimeDTO:
    bot_nick: str
    channel_name: str
    occurred_at: datetime
