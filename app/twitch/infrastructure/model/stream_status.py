from dataclasses import dataclass
from typing import Optional, List


@dataclass
class StreamData:
    id: str
    user_id: str
    user_login: str
    user_name: str
    game_id: str
    game_name: str
    type: str
    title: str
    viewer_count: int
    started_at: str
    language: str
    thumbnail_url: str
    tag_ids: List[str]
    is_mature: bool


@dataclass
class StreamStatus:
    is_online: bool
    stream_data: Optional[StreamData] = None
