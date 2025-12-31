from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class UserData(BaseModel):
    id: str
    login: str
    display_name: str


class UsersResponse(BaseModel):
    data: List[UserData] = Field(default_factory=list)


class StreamDataModel(BaseModel):
    id: str
    user_id: str
    user_login: str
    user_name: str
    game_id: Optional[str] = None
    game_name: Optional[str] = None
    type: Optional[str] = None
    title: Optional[str] = None
    viewer_count: Optional[int] = None
    started_at: datetime
    language: Optional[str] = None
    thumbnail_url: Optional[str] = None
    tag_ids: List[str] = Field(default_factory=list)
    is_mature: Optional[bool] = False


class StreamsResponse(BaseModel):
    data: List[StreamDataModel] = Field(default_factory=list)


class FollowerData(BaseModel):
    user_id: str
    user_name: str
    user_login: str
    followed_at: datetime


class FollowersResponse(BaseModel):
    data: List[FollowerData] = Field(default_factory=list)
    total: Optional[int] = None
    pagination: Optional[dict] = None


class Chatter(BaseModel):
    user_login: str


class ChattersResponse(BaseModel):
    data: List[Chatter] = Field(default_factory=list)
