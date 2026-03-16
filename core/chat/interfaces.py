from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ChatMessage:
    author: str
    text: str
    author_id: str


class ChatContext:
    def __init__(self, channel: str):
        self.channel = channel


CommandHandler = Callable[[ChatContext, ChatMessage], Awaitable[None]]


class CommandRouter(Protocol):
    def register(self, name: str, handler: CommandHandler) -> None: ...
    async def dispatch(self, message: ChatMessage, ctx: ChatContext) -> bool: ...


class ChatClient(Protocol):
    def set_router(self, router: CommandRouter) -> None: ...
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
