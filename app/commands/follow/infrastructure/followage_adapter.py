from app.commands.follow.application.followage_port import FollowagePort
from app.commands.follow.application.model import FollowageInfo
from app.platform.streaming import StreamingPlatformPort


class FollowageAdapter(FollowagePort):
    def __init__(self, platform: StreamingPlatformPort):
        self._platform = platform

    async def get_followage(self, channel_name: str, user_id: str) -> FollowageInfo | None:
        return await self._platform.get_followage(channel_name, user_id)
