from app.commands.follow.application.followage_port import FollowagePort
from app.commands.follow.model import FollowageInfo
from app.twitch.infrastructure.twitch_api_service import TwitchApiService


class FollowageAdapter(FollowagePort):
    def __init__(self, twitch_api_service: TwitchApiService):
        self._twitch_api_service = twitch_api_service

    async def get_followage(self, channel_name: str, user_id: str) -> FollowageInfo | None:
        return await self._twitch_api_service.get_followage(channel_name, user_id)
