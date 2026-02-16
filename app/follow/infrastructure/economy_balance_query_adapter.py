from app.economy.domain.economy_policy import EconomyPolicy
from app.follow.application.user_balance_port import BalanceDetail, UserBalanceQueryPort


class EconomyBalanceQueryAdapter(UserBalanceQueryPort):
    def __init__(self, economy_policy: EconomyPolicy):
        self._economy_policy = economy_policy

    def get_balance(self, channel_name: str, user_name: str) -> BalanceDetail:
        user_balance = self._economy_policy.get_user_balance(channel_name, user_name)
        return BalanceDetail(balance=user_balance.balance)
