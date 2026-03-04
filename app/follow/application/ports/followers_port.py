from typing import Protocol

from app.follow.application.models.follower import ChannelFollowerDTO


class FollowersPort(Protocol):
    async def get_channel_followers(self, channel_name: str) -> list[ChannelFollowerDTO]: ...
