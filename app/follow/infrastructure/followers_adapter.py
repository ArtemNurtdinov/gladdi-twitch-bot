from typing import List

from app.follow.application.model import ChannelFollowerDTO
from app.follow.application.followers_port import FollowersPort
from app.twitch.infrastructure.twitch_api_service import TwitchApiService


class FollowersAdapter(FollowersPort):

    def __init__(self, twitch_api_service: TwitchApiService):
        self._twitch_api_service = twitch_api_service

    async def get_channel_followers(self, channel_login: str) -> List[ChannelFollowerDTO]:
        return await self._twitch_api_service.get_channel_followers(channel_login)
