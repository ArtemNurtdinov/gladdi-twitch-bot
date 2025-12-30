from typing import Optional

from app.twitch.application.interaction.follow.followage_port import FollowagePort
from app.twitch.application.interaction.follow.model import FollowageInfo
from app.twitch.infrastructure.twitch_api_service import TwitchApiService


class FollowageAdapter(FollowagePort):
    def __init__(self, twitch_api_service: TwitchApiService):
        self._twitch_api_service = twitch_api_service

    async def get_followage(self, channel_login: str, user_id: str) -> Optional[FollowageInfo]:
        return await self._twitch_api_service.get_followage(channel_login, user_id)

