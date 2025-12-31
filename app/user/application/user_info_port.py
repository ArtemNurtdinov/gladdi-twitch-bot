from typing import Protocol

from app.user.application.model import UserInfoDTO


class UserInfoPort(Protocol):
    async def get_user_by_login(self, login: str) -> UserInfoDTO | None: ...
