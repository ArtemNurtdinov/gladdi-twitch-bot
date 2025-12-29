from typing import Optional

from app.twitch.application.interaction.follow.dto import FollowageInfo
from app.twitch.application.interaction.follow.followage_provider import FollowageProvider


class GetFollowageUseCase:

    def __init__(self, followage_provider: FollowageProvider):
        self._followage_provider = followage_provider

    async def get_followage(self, channel_login: str, user_id: str) -> Optional[FollowageInfo]:
        return await self._followage_provider.get_followage(
            channel_login=channel_login,
            user_id=user_id
        )