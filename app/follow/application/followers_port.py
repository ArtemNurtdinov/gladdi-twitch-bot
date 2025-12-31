from typing import Protocol, List

from app.follow.application.model import ChannelFollowerDTO


class FollowersPort(Protocol):

    async def get_channel_followers(self, channel_name: str) -> List[ChannelFollowerDTO]:
        ...
