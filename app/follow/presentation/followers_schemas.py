from datetime import datetime

from pydantic import BaseModel, Field


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


class FollowerSessionStreamInfo(BaseModel):
    id: int
    title: str | None = None
    game_name: str | None = None
    started_at: datetime
    ended_at: datetime | None = None


class FollowerSessionItem(BaseModel):
    id: int
    stream_id: int
    channel_name: str
    user_name: str
    session_start: datetime | None = None
    session_end: datetime | None = None
    total_minutes: int
    last_activity: datetime | None = None
    is_watching: bool
    rewards_claimed: str
    last_reward_claimed: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    stream: FollowerSessionStreamInfo | None = None


class FollowerDetailResponse(FollowerResponse):
    balance: int
    sessions: list[FollowerSessionItem] = Field(default_factory=list, description="Сессии просмотра пользователя")


class FollowersListResponse(BaseModel):
    followers: list[FollowerResponse]
