from abc import ABC, abstractmethod


class NotificationRepository(ABC):
    @abstractmethod
    async def send_notification(self, chat_id: int, text: str) -> None: ...
