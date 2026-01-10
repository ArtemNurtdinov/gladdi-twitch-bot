from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class UserData(BaseModel):
    id: str
    login: str
    display_name: str


class UsersResponse(BaseModel):
    data: list[UserData] = Field(default_factory=list)


class StreamDataModel(BaseModel):
    id: str
    user_id: str
    user_login: str
    user_name: str
    game_id: str | None = None
    game_name: str | None = None
    type: str | None = None
    title: str | None = None
    viewer_count: int | None = None
    started_at: datetime
    language: str | None = None
    thumbnail_url: str | None = None
    tag_ids: list[str] = Field(default_factory=list)
    is_mature: bool | None = False


class StreamsResponse(BaseModel):
    data: list[StreamDataModel] = Field(default_factory=list)


class FollowerData(BaseModel):
    user_id: str
    user_name: str
    user_login: str
    followed_at: datetime


class FollowersResponse(BaseModel):
    data: list[FollowerData] = Field(default_factory=list)
    total: int | None = None
    pagination: dict | None = None


class Chatter(BaseModel):
    user_login: str


class ChattersResponse(BaseModel):
    data: list[Chatter] = Field(default_factory=list)
