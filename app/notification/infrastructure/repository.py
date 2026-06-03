import asyncio

import httpx
import telegram
from telegram.error import NetworkError, TimedOut

from app.core.logger.domain.logger import Logger
from app.notification.domain.repository import NotificationRepository

_RETRYABLE_ERRORS = (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout, NetworkError, TimedOut, TimeoutError)
_MAX_ATTEMPTS = 3


class NotificationRepositoryImpl(NotificationRepository):
    def __init__(self, bot: telegram.Bot, logger: Logger):
        self._bot = bot
        self._logger = logger.create_child(__name__)

    async def send_notification(self, chat_id: int, text: str) -> None:
        last_error: Exception | None = None

        for attempt in range(1, _MAX_ATTEMPTS + 1):
            try:
                await self._bot.send_message(chat_id=chat_id, text=text)
                return
            except _RETRYABLE_ERRORS as error:
                last_error = error
                if attempt < _MAX_ATTEMPTS:
                    delay_seconds = 2 ** (attempt - 1)
                    self._logger.log_error(
                        f"Telegram send failed (attempt {attempt}/{_MAX_ATTEMPTS}): {error}. "
                        f"Retrying in {delay_seconds}s..."
                    )
                    await asyncio.sleep(delay_seconds)

        if last_error is not None:
            raise last_error
