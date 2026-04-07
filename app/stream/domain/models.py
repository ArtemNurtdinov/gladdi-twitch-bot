from dataclasses import dataclass
from datetime import datetime

from app.stream.domain.model.info import StreamInfo


@dataclass(frozen=True)
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


@dataclass(frozen=True)
class StreamDetail:
    stream: StreamInfo
    sessions: list[StreamViewerSessionInfo]
    total_watch_minutes: int
    total_messages: int
