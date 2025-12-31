from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class FollowersSyncJobDTO:
    channel_name: str
    occurred_at: datetime


@dataclass(frozen=True)
class ChannelFollowerDTO:
    user_id: str
    user_name: str
    display_name: str
    followed_at: datetime
