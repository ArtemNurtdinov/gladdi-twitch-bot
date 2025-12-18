from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class StreamStatistics:
    total_messages: int
    unique_users: int
    top_user: str | None
    total_battles: int
    top_winner: str | None


@dataclass
class StreamInfo:
    id: int
    channel_name: str
    started_at: datetime
    ended_at: Optional[datetime]
    game_name: Optional[str]
    title: Optional[str]
    is_active: bool
    max_concurrent_viewers: Optional[int]
    total_viewers: Optional[int]
    created_at: datetime
    updated_at: datetime


@dataclass
class StreamViewerSessionInfo:
    id: int
    stream_id: int
    channel_name: str
    user_name: str
    session_start: Optional[datetime]
    session_end: Optional[datetime]
    total_minutes: int
    last_activity: Optional[datetime]
    is_watching: bool
    rewards_claimed: str
    last_reward_claimed: Optional[datetime]
    created_at: datetime
    updated_at: datetime
