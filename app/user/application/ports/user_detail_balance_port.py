from typing import Protocol

from app.user.application.model.user_detail_models import UserBalanceInfo


class UserDetailBalancePort(Protocol):
    def get_balance(self, channel_name: str, user_name: str) -> UserBalanceInfo: ...
