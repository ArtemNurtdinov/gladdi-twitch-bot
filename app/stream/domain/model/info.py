from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
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
