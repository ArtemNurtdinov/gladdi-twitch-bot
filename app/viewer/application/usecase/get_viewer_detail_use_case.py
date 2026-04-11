from app.viewer.application.model.viewer_detail_models import ViewerDetailResult
from app.viewer.application.port.viewer_detail_balance_port import ViewerDetailBalancePort
from app.viewer.application.port.viewer_detail_info_port import ViewerDetailInfoPort
from app.viewer.application.port.viewer_detail_sessions_port import ViewerDetailSessionsPort


class GetViewerDetailUseCase:
    def __init__(
        self,
        user_detail_info_port: ViewerDetailInfoPort,
        balance_port: ViewerDetailBalancePort,
        sessions_port: ViewerDetailSessionsPort,
    ):
        self._info_port = user_detail_info_port
        self._balance_port = balance_port
        self._sessions_port = sessions_port

    def handle(self, channel_name: str, user_name: str) -> ViewerDetailResult:
        user_info = self._info_port.get(channel_name, user_name)
        balance = self._balance_port.get_balance(channel_name, user_name)
        sessions = self._sessions_port.get_user_sessions(channel_name, user_name)
        return ViewerDetailResult(user_info=user_info, balance=balance, sessions=sessions)
