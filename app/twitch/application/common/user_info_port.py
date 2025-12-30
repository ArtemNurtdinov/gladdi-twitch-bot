from typing import Optional, Protocol

from app.twitch.application.common.model import UserInfoDTO


class UserInfoPort(Protocol):

    async def get_user_by_login(self, login: str) -> Optional[UserInfoDTO]:
        ...
