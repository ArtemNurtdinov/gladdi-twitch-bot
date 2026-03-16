from abc import ABC, abstractmethod

from app.platform.command.domain.command_handler import CommandHandler


class CommandRouter(ABC):
    @abstractmethod
    def register_command_handler(self, name: str, handler: CommandHandler) -> None: ...

    @abstractmethod
    def get_command_handler(self, message: str) -> CommandHandler | None: ...
