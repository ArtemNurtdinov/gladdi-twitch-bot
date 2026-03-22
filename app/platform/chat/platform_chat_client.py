from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from app.platform.command.domain.command_router import CommandRouter


class ChatEventsHandler(Protocol):
    async def handle(self, channel_name: str, display_name: str, message: str, bot_name: str) -> None: ...


class PlatformChatClient(ABC):
    @abstractmethod
    def set_router(self, router: CommandRouter): ...
    @abstractmethod
    def set_chat_event_handler(self, handler: ChatEventsHandler): ...
    @abstractmethod
    async def send_channel_message(self, message: str): ...
    @abstractmethod
    async def start_chat(self): ...
    @abstractmethod
    async def stop_chat(self): ...
