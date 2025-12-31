from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RestoreStreamJobDTO:
    channel_name: str


@dataclass(frozen=True)
class StatusJobDTO:
    channel_name: str


@dataclass(frozen=True)
class StreamDataDTO:
    id: str | None
    user_id: str | None
    user_login: str | None
    user_name: str | None
    game_id: str | None
    game_name: str | None
    type: str | None
    title: str | None
    viewer_count: int | None
    started_at: datetime | None
    language: str | None
    thumbnail_url: str | None
    tag_ids: list[str]
    is_mature: bool | None


@dataclass(frozen=True)
class StreamStatusDTO:
    is_online: bool
    stream_data: StreamDataDTO | None = None
