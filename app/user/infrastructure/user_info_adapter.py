
from app.platform.streaming import StreamingPlatformPort
from app.user.application.model import UserInfoDTO
from app.user.application.user_info_port import UserInfoPort


class UserInfoAdapter(UserInfoPort):
    def __init__(self, platform: StreamingPlatformPort):
        self._platform = platform

    async def get_user_by_login(self, login: str) -> UserInfoDTO | None:
        return await self._platform.get_user_by_login(login)
