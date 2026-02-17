from app.economy.domain.economy_policy import EconomyPolicy
from app.user.application.model.user_detail_models import UserBalanceInfo
from app.user.application.ports.user_detail_balance_port import UserDetailBalancePort


class EconomyUserBalanceAdapter(UserDetailBalancePort):
    def __init__(self, economy_policy: EconomyPolicy):
        self._economy_policy = economy_policy

    def get_balance(self, channel_name: str, user_name: str) -> UserBalanceInfo:
        ub = self._economy_policy.get_user_balance(channel_name, user_name)
        return UserBalanceInfo(balance=ub.balance, total_earned=ub.total_earned, total_spent=ub.total_spent)
