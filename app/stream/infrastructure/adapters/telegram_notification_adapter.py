import telegram

from app.stream.application.port.notification_port import NotificationPort


class TelegramNotificationAdapter(NotificationPort):
    def __init__(self, bot: telegram.Bot):
        self._bot = bot

    async def send_notification(self, chat_id: int, text: str) -> None:
        await self._bot.send_message(chat_id=chat_id, text=text)
