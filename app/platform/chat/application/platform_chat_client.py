from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from app.core.logger.domain.logger import Logger
from app.platform.auth.platform_auth import PlatformAuth
from app.platform.chat.application.handle_chat_message_use_case import HandleChatMessageUseCase
from app.platform.chat.application.handle_reply_use_case import HandleReplyUseCase
from app.platform.chat.application.model import ChatMessageDTO
from app.platform.command.domain.command_router import CommandRouter


class PlatformChatClient(ABC):
    def __init__(
        self,
        auth: PlatformAuth,
        handle_chat_message_use_case: HandleChatMessageUseCase,
        handle_reply_use_case: HandleReplyUseCase,
        command_router: CommandRouter,
        channel_name: str,
        bot_name: str,
        command_prefix: str,
        logger: Logger,
    ):
        self.auth = auth
        self._handle_chat_message_use_case = handle_chat_message_use_case
        self._handle_reply_use_case = handle_reply_use_case
        self._command_router = command_router
        self.channel_name = channel_name
        self.bot_name = bot_name
        self.command_prefix = command_prefix
        self._logger = logger.create_child(__name__)

    async def handle_message(self, user_name: str, message: str):
        if await self._command_handled(user_name, message):
            return

        if self._is_self_message(user_name):
            return

        if message.startswith(self.command_prefix):
            return

        chat_message = ChatMessageDTO(
            channel_name=self.channel_name,
            display_name=user_name,
            user_name=user_name.lower(),
            message=message,
            bot_name=self.bot_name,
            occurred_at=datetime.utcnow(),
        )

        try:
            if self.is_reply_message(message):
                self._logger.log_info(f"handle reply message: {message}")
                result = await self._handle_reply_use_case.handle(chat_message)
                await self.send_channel_message(result)
                return
            result = await self._handle_chat_message_use_case.handle(chat_message)
            if result:
                self._logger.log_info(f"handle chat message: {message}")
                await self.send_channel_message(result)
        except Exception:
            pass

    async def _command_handled(self, user_name: str, message: str) -> bool:
        command_handler = self._command_router.get_command_handler(message)
        if command_handler is None:
            return False
        try:
            result = await command_handler.handle(self.channel_name, user_name, message)
            await self.send_channel_message(result)
            return True
        except Exception:
            pass
        return False

    def _is_self_message(self, user_name: str) -> bool:
        if user_name.lower() == self.bot_name.lower():
            return True
        else:
            return False

    @abstractmethod
    async def send_channel_message(self, message: str): ...

    @abstractmethod
    def is_reply_message(self, message: str) -> bool: ...

    @abstractmethod
    async def start_chat(self): ...

    @abstractmethod
    async def stop_chat(self): ...
