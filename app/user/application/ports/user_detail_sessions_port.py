from typing import Protocol

from app.user.application.model.user_detail_models import UserSessionDetail


class UserDetailSessionsPort(Protocol):
    def get_user_sessions(self, channel_name: str, user_name: str) -> list[UserSessionDetail]: ...
