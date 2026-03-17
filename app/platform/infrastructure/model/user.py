from __future__ import annotations

from pydantic import BaseModel, Field


class UserData(BaseModel):
    id: str
    login: str
    display_name: str


class UsersResponse(BaseModel):
    data: list[UserData] = Field(default_factory=list)
