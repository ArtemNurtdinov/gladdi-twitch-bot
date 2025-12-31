from typing import Protocol, List

from app.twitch.application.common.model import ChannelFollowerDTO


class FollowersPort(Protocol):
    async def get_channel_followers(self, channel_login: str) -> List[ChannelFollowerDTO]:
        ...


