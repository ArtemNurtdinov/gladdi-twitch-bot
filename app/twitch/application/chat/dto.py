from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ChatMessageDTO:
    channel_name: str
    display_name: str
    user_name: str
    message: str
    bot_nick: str
    occurred_at: datetime
