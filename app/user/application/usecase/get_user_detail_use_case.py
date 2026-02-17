from app.user.application.model.user_detail_models import UserDetailResult
from app.user.application.ports.user_detail_balance_port import UserDetailBalancePort
from app.user.application.ports.user_detail_info_port import UserDetailInfoPort
from app.user.application.ports.user_detail_sessions_port import UserDetailSessionsPort


class GetUserDetailUseCase:
    def __init__(
        self,
        user_detail_info_port: UserDetailInfoPort,
        balance_port: UserDetailBalancePort,
        sessions_port: UserDetailSessionsPort,
    ):
        self._info_port = user_detail_info_port
        self._balance_port = balance_port
        self._sessions_port = sessions_port

    def handle(self, channel_name: str, user_name: str) -> UserDetailResult:
        user_info = self._info_port.get(channel_name, user_name)
        balance = self._balance_port.get_balance(channel_name, user_name)
        sessions = self._sessions_port.get_user_sessions(channel_name, user_name)
        return UserDetailResult(user_info=user_info, balance=balance, sessions=sessions)
