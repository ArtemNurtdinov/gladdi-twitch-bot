from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ChannelFollower:
    id: int
    channel_name: str
    user_id: str
    user_name: str
    display_name: str
    followed_at: Optional[datetime]
    first_seen_at: datetime
    last_seen_at: datetime
    unfollowed_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime
