from dataclasses import dataclass
from datetime import datetime


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
    ended_at: datetime | None
    game_name: str | None
    title: str | None
    is_active: bool
    max_concurrent_viewers: int | None
    total_viewers: int | None
    created_at: datetime
    updated_at: datetime


@dataclass
class StreamViewerSessionInfo:
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
    created_at: datetime
    updated_at: datetime


@dataclass
class StreamDetail:
    stream: StreamInfo
    sessions: list[StreamViewerSessionInfo]
