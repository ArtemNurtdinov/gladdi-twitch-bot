from abc import ABC, abstractmethod


class CommandHandler(ABC):
    @abstractmethod
    async def handle_command(self, channel_name: str, user_name: str, user_message: str): ...
