from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class ChatMessage:
    channel: str
    author: str
    text: str
    author_id: str


@runtime_checkable
class ChatContext(Protocol):
    @property
    def channel(self) -> str: ...

    @property
    def author(self) -> str: ...

    async def reply(self, text: str) -> None: ...
    async def send_channel(self, text: str) -> None: ...


CommandHandler = Callable[[ChatContext, ChatMessage], Awaitable[None]]


class CommandRouter(Protocol):
    def register(self, name: str, handler: CommandHandler) -> None: ...
    async def dispatch(self, message: ChatMessage, ctx: ChatContext) -> bool: ...


class ChatClient(Protocol):
    def set_router(self, router: CommandRouter) -> None: ...
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
