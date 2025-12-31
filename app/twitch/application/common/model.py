from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class StreamDataDTO:
    id: Optional[str]
    user_id: Optional[str]
    user_login: Optional[str]
    user_name: Optional[str]
    game_id: Optional[str]
    game_name: Optional[str]
    type: Optional[str]
    title: Optional[str]
    viewer_count: Optional[int]
    started_at: Optional[datetime]
    language: Optional[str]
    thumbnail_url: Optional[str]
    tag_ids: list[str]
    is_mature: Optional[bool]


@dataclass(frozen=True)
class StreamStatusDTO:
    is_online: bool
    stream_data: Optional[StreamDataDTO] = None


@dataclass(frozen=True)
class UserInfoDTO:
    id: str
    login: str
    display_name: str


@dataclass(frozen=True)
class ChannelFollowerDTO:
    user_id: str
    user_name: str  # login
    display_name: str  # display name from Twitch
    followed_at: datetime