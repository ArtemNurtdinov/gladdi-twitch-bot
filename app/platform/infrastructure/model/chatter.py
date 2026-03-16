from __future__ import annotations

from pydantic import BaseModel, Field


class Chatter(BaseModel):
    user_login: str


class ChattersResponse(BaseModel):
    data: list[Chatter] = Field(default_factory=list)
