from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ChatMessage:
    author: str
    text: str


class ChatContext:
    def __init__(self, channel: str):
        self.channel = channel


class CommandHandler(ABC):
    @abstractmethod
    async def handle_command(self, channel_name: str, user_name: str, user_message: str): ...


class CommandRouter(ABC):
    @abstractmethod
    def register(self, name: str, handler: CommandHandler) -> None: ...
    @abstractmethod
    async def dispatch_command_handler(self, channel_name: str, user_name: str, message: str) -> bool: ...
