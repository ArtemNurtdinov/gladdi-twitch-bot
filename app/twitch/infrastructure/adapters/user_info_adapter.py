from typing import Optional

from app.twitch.application.common.model import UserInfoDTO
from app.twitch.application.common.user_info_port import UserInfoPort
from app.twitch.infrastructure.twitch_api_service import TwitchApiService


class UserInfoAdapter(UserInfoPort):
    def __init__(self, twitch_api_service: TwitchApiService):
        self._twitch_api_service = twitch_api_service

    async def get_user_by_login(self, login: str) -> Optional[UserInfoDTO]:
        return await self._twitch_api_service.get_user_by_login(login)

