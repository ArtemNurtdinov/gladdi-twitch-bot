from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class FollowerResponse(BaseModel):
    id: int
    channel_name: str
    user_id: str
    user_name: str
    display_name: str
    followed_at: Optional[datetime] = None
    first_seen_at: datetime
    last_seen_at: datetime
    unfollowed_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class FollowersListResponse(BaseModel):
    followers: List[FollowerResponse]


