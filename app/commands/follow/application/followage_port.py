from typing import Protocol

from app.commands.follow.application.model import FollowageInfo
from app.follow.application.model import ChannelFollowerDTO


class FollowagePort(Protocol):
    async def get_followage(self, channel_name: str, user_id: str) -> FollowageInfo | None: ...
    async def get_channel_followers(self, channel_name: str) -> list[ChannelFollowerDTO]: ...
