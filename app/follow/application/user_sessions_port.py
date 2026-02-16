from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class StreamBrief:
    id: int
    title: str | None
    game_name: str | None
    started_at: datetime
    ended_at: datetime | None


@dataclass(frozen=True)
class SessionDetail:
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
    stream: StreamBrief | None


class UserSessionsQueryPort(Protocol):
    def get_user_sessions(self, channel_name: str, user_name: str) -> list[SessionDetail]: ...
