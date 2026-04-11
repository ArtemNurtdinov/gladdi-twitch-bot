from typing import Protocol

from app.viewer.application.model.viewer_detail_models import ViewerBalanceInfo


class ViewerDetailBalancePort(Protocol):
    def get_balance(self, channel_name: str, user_name: str) -> ViewerBalanceInfo: ...
