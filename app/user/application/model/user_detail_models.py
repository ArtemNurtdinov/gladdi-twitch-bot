from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class UserStreamBrief:
    id: int
    title: str | None
    game_name: str | None
    started_at: datetime
    ended_at: datetime | None


@dataclass(frozen=True)
class UserSessionDetail:
    id: int
    stream_id: int
    channel_name: str
    user_name: str
    session_start: datetime | None
    session_end: datetime | None
    total_minutes: int
    last_activity: datetime | None
    is_watching: bool
    rewards_claimed: str
    last_reward_claimed: datetime | None
    created_at: datetime | None
    updated_at: datetime | None
    stream: UserStreamBrief | None


@dataclass
class UserDetailInfo:
    channel_name: str
    user_name: str
    display_name: str
    followed_at: datetime | None
    first_seen_at: datetime | None
    last_seen_at: datetime | None
    unfollowed_at: datetime | None
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None


@dataclass(frozen=True)
class UserBalanceInfo:
    balance: int
    total_earned: int
    total_spent: int


@dataclass
class UserDetailResult:
    user_info: UserDetailInfo
    balance: UserBalanceInfo
    sessions: list[UserSessionDetail]
