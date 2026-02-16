from dataclasses import dataclass
from datetime import datetime


@dataclass
class ChannelFollower:
    id: int
    channel_name: str
    user_id: str
    user_name: str
    display_name: str
    followed_at: datetime | None
    first_seen_at: datetime | None
    last_seen_at: datetime | None
    unfollowed_at: datetime | None
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None
