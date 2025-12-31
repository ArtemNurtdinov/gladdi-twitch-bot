from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TopDTO:
    channel_name: str
    bot_nick: str
    occurred_at: datetime
    limit: int


@dataclass(frozen=True)
class BottomDTO:
    channel_name: str
    bot_nick: str
    occurred_at: datetime
    limit: int

