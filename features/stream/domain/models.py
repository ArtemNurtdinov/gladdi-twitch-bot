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
