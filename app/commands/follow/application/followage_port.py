from typing import Protocol

from app.commands.follow.application.model import FollowageInfo


class FollowagePort(Protocol):
    async def get_followage(self, channel_name: str, user_id: str) -> FollowageInfo | None: ...
