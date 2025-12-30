from typing import Optional

from app.twitch.application.interaction.follow.followage_port import FollowagePort
from app.twitch.application.interaction.follow.model import FollowageInfo


class GetFollowageUseCase:

    def __init__(self, followage_port: FollowagePort):
        self._followage_port = followage_port

    async def get_followage(self, channel_login: str, user_id: str) -> Optional[FollowageInfo]:
        return await self._followage_port.get_followage(
            channel_login=channel_login,
            user_id=user_id
        )
