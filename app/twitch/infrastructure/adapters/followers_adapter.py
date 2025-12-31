from typing import List

from app.twitch.application.common.followers_port import FollowersPort
from app.twitch.application.common.model import ChannelFollowerDTO
from app.twitch.infrastructure.twitch_api_service import TwitchApiService


class FollowersAdapter(FollowersPort):
    def __init__(self, twitch_api_service: TwitchApiService):
        self._twitch_api_service = twitch_api_service

    async def get_channel_followers(self, channel_login: str) -> List[ChannelFollowerDTO]:
        return await self._twitch_api_service.get_channel_followers(channel_login)


