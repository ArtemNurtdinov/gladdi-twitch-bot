from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PostPeriodicMessagesDTO:
    channel_name: str
    bot_nick: str
    occurred_at: datetime
