from abc import ABC, abstractmethod

from app.platform.command.domain.command_handler import CommandHandler


class CommandRouter(ABC):
    @abstractmethod
    def register(self, name: str, handler: CommandHandler) -> None: ...
    @abstractmethod
    async def dispatch_command_handler(self, channel_name: str, user_name: str, message: str) -> bool: ...
