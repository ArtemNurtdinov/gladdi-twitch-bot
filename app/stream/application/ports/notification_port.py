from typing import Protocol


class NotificationPort(Protocol):
    async def send_message(self, chat_id: int, text: str) -> None: ...
