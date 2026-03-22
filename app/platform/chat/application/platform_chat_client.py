from __future__ import annotations

from abc import ABC, abstractmethod

from app.platform.chat.application.chat_events_handler import ChatEventsHandler
from app.platform.command.domain.command_router import CommandRouter


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
