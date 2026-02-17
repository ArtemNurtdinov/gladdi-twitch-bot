from typing import Protocol

from app.user.application.model.user_detail_models import UserDetailInfo


class UserDetailInfoPort(Protocol):
    def get(self, channel_name: str, user_name: str) -> UserDetailInfo: ...
