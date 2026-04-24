from abc import ABC, abstractmethod

from app.platform.command.domain.command_handler import CommandHandler


class CommandRouter(ABC):
    @abstractmethod
    def apply_bot_name(self, bot_name: str, battle_waiting_user: dict[str, str | None]) -> None: ...

    @abstractmethod
    def register_command_handler(self, name: str, handler: CommandHandler) -> None: ...

    @abstractmethod
    def get_command_handler(self, message: str) -> CommandHandler | None: ...
