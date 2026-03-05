from app.follow.application.models.follower import ChannelFollowerDTO
from app.follow.application.ports.followers_port import FollowersPort
from app.platform.streaming import StreamingPlatformPort


class FollowersAdapter(FollowersPort):
    def __init__(self, platform: StreamingPlatformPort):
        self._platform = platform

    async def get_channel_followers(self, channel_name: str) -> list[ChannelFollowerDTO]:
        return await self._platform.get_channel_followers(channel_name)
