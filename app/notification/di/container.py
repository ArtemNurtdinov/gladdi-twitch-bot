import telegram
from telegram.request import HTTPXRequest

from app.notification.domain.repository import NotificationRepository
from app.notification.infrastructure.repository import NotificationRepositoryImpl


class NotificationContainer:
    def __init__(self, tg_bot_token: str):
        self._tg_bot_token = tg_bot_token

    def notification_repository(self) -> NotificationRepository:
        http_request = HTTPXRequest(connection_pool_size=10, pool_timeout=10)
        tg_bot = telegram.Bot(token=self._tg_bot_token, request=http_request)
        return NotificationRepositoryImpl(tg_bot)
