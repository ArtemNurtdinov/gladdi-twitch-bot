import telegram
from telegram.request import HTTPXRequest

from app.notification.domain.repository import NotificationRepository
from app.notification.infrastructure.repository import NotificationRepositoryImpl


def provide_telegram_bot(tg_bot_token: str) -> telegram.Bot:
    http_request = HTTPXRequest(connection_pool_size=10, pool_timeout=10)
    return telegram.Bot(token=tg_bot_token, request=http_request)


def provide_notification_repository(bot: telegram.Bot) -> NotificationRepository:
    return NotificationRepositoryImpl(bot)
