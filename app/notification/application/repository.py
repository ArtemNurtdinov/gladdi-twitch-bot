from typing import Protocol


class NotificationRepository(Protocol):
    async def send_notification(self, chat_id: int, text: str) -> None: ...
