from app.follow.application.followers_port import FollowersPort
from app.follow.application.model import ChannelFollowerDTO
from app.platform.streaming import StreamingPlatformPort


class FollowersAdapter(FollowersPort):
    def __init__(self, platform: StreamingPlatformPort):
        self._platform = platform

    async def get_channel_followers(self, channel_name: str) -> list[ChannelFollowerDTO]:
        return await self._platform.get_channel_followers(channel_name)
