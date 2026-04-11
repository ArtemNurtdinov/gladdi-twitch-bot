from app.economy.domain.economy_policy import EconomyPolicy
from app.viewer.application.model.viewer_detail_models import ViewerBalanceInfo
from app.viewer.application.port.viewer_detail_balance_port import ViewerDetailBalancePort


class EconomyViewerBalanceAdapter(ViewerDetailBalancePort):
    def __init__(self, economy_policy: EconomyPolicy):
        self._economy_policy = economy_policy

    def get_balance(self, channel_name: str, user_name: str) -> ViewerBalanceInfo:
        ub = self._economy_policy.get_user_balance(channel_name, user_name)
        return ViewerBalanceInfo(balance=ub.balance, total_earned=ub.total_earned, total_spent=ub.total_spent)
