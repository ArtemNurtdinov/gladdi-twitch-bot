import telegram
from telegram.request import HTTPXRequest

from app.core.logger.domain.logger import Logger
from app.notification.domain.repository import NotificationRepository
from app.notification.infrastructure.repository import NotificationRepositoryImpl, NullNotificationRepository

_CONNECT_TIMEOUT_SECONDS = 30.0
_READ_TIMEOUT_SECONDS = 30.0
_WRITE_TIMEOUT_SECONDS = 30.0
_POOL_TIMEOUT_SECONDS = 30.0


class NotificationContainer:
    def __init__(self, tg_bot_token: str | None, group_id: int | None, logger: Logger, proxy_url: str | None = None):
        self._tg_bot_token = tg_bot_token
        self._group_id = group_id
        self._logger = logger
        self._proxy_url = proxy_url

    def notification_repository(self) -> NotificationRepository:
        if not self._tg_bot_token or self._group_id is None:
            self._logger.log_info("Telegram не настроен, уведомления отключены")
            return NullNotificationRepository()
        http_request = HTTPXRequest(
            connection_pool_size=10,
            connect_timeout=_CONNECT_TIMEOUT_SECONDS,
            read_timeout=_READ_TIMEOUT_SECONDS,
            write_timeout=_WRITE_TIMEOUT_SECONDS,
            pool_timeout=_POOL_TIMEOUT_SECONDS,
            proxy_url=self._proxy_url,
        )
        tg_bot = telegram.Bot(token=self._tg_bot_token, request=http_request)
        return NotificationRepositoryImpl(tg_bot, self._logger)
