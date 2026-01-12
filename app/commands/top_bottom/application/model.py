from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TopDTO:
    command_prefix: str
    command_name: str
    channel_name: str
    user_name: str
    bot_nick: str
    occurred_at: datetime
    limit: int


@dataclass(frozen=True)
class BottomDTO:
    command_prefix: str
    command_name: str
    channel_name: str
    user_name: str
    bot_nick: str
    occurred_at: datetime
    limit: int
