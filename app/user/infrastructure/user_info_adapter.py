
from app.twitch.infrastructure.twitch_api_service import TwitchApiService
from app.user.application.model import UserInfoDTO
from app.user.application.user_info_port import UserInfoPort


class UserInfoAdapter(UserInfoPort):
    def __init__(self, twitch_api_service: TwitchApiService):
        self._twitch_api_service = twitch_api_service

    async def get_user_by_login(self, login: str) -> UserInfoDTO | None:
        return await self._twitch_api_service.get_user_by_login(login)
