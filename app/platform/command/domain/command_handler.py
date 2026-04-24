from abc import ABC, abstractmethod


class CommandHandler(ABC):
    @abstractmethod
    def apply_bot_name(self, bot_name) -> None: ...

    @abstractmethod
    async def handle(self, channel_name: str, user_name: str, message: str) -> str: ...
