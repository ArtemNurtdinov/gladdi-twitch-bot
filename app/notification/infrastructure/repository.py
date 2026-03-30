import telegram

from app.notification.domain.repository import NotificationRepository


class NotificationRepositoryImpl(NotificationRepository):
    def __init__(self, bot: telegram.Bot):
        self._bot = bot

    async def send_notification(self, chat_id: int, text: str) -> None:
        await self._bot.send_message(chat_id=chat_id, text=text)
