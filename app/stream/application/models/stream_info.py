from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class StreamInfoDTO:
    id: str | None
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
