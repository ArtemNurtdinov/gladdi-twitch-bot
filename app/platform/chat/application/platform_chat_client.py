from __future__ import annotations

from abc import ABC, abstractmethod

from app.platform.auth.platform_auth import PlatformAuth
from app.platform.chat.application.chat_event_handler import ChatEventsHandler
from app.platform.command.domain.command_router import CommandRouter


class PlatformChatClient(ABC):
    _command_router: CommandRouter | None = None
    _chat_events_handler: ChatEventsHandler | None = None

    def __init__(self, auth: PlatformAuth, chat_events_handler: ChatEventsHandler, channel_name: str, bot_name: str, command_prefix: str):
        self.auth = auth
        self.chat_events_handler = chat_events_handler
        self.channel_name = channel_name
        self.bot_name = bot_name
        self.command_prefix = command_prefix

    def set_command_router(self, command_router: CommandRouter):
        self._command_router = command_router

    def set_chat_event_handler(self, chat_events_handler: ChatEventsHandler):
        self._chat_events_handler = chat_events_handler

    async def handle_message(self, user_name: str, message: str):
        if self._command_router is None:
            return

        command_handler = self._command_router.get_command_handler(message)

        if command_handler:
            try:
                result = await command_handler.handle(self.channel_name, user_name, message)
                if result:
                    await self.send_channel_message(result)
            except Exception:
                pass
            return

        if self._is_self_message(user_name):
            return

        if message.startswith(self.command_prefix):
            return

        try:
            result = await self._chat_events_handler.handle(self.channel_name, user_name, message, self.bot_name)
            if result:
                await self.send_channel_message(result)
        except Exception:
            pass

    def _is_self_message(self, user_name: str) -> bool:
        if user_name.lower() == self.bot_name.lower():
            return True
        else:
            return False

    @abstractmethod
    async def send_channel_message(self, message: str): ...

    @abstractmethod
    async def start_chat(self): ...

    @abstractmethod
    async def stop_chat(self): ...
