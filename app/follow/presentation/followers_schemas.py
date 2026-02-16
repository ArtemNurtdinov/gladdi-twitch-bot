from datetime import datetime

from pydantic import BaseModel


class FollowerResponse(BaseModel):
    id: int
    channel_name: str
    user_id: str
    user_name: str
    display_name: str
    followed_at: datetime | None = None
    first_seen_at: datetime
    last_seen_at: datetime
    unfollowed_at: datetime | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class FollowerDetailResponse(FollowerResponse):
    balance: int


class FollowersListResponse(BaseModel):
    followers: list[FollowerResponse]
