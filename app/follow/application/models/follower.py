from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ChannelFollowerDTO:
    user_id: str
    user_name: str
    display_name: str
    followed_at: datetime
