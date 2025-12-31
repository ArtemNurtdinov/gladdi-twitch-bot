from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class FollowageInfo:
    user_id: str
    user_name: str
    user_login: str
    followed_at: datetime


@dataclass(frozen=True)
class FollowageDTO:
    channel_name: str
    display_name: str
    user_name: str
    bot_nick: str
    occurred_at: datetime
    user_id: str
