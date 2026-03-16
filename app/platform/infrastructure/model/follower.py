from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class FollowerData(BaseModel):
    user_id: str
    user_name: str
    user_login: str
    followed_at: datetime


class FollowersResponse(BaseModel):
    data: list[FollowerData] = Field(default_factory=list)
    total: int | None = None
    pagination: dict | None = None
