from abc import ABC, abstractmethod


class CommandHandler(ABC):
    @abstractmethod
    async def handle(self, channel_name: str, user_name: str, message: str) -> str | None: ...
