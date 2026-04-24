from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime

from app.core.logger.domain.logger import Logger
from app.platform.chat.application.model.message import ChatMessageDTO
from app.platform.chat.application.usecase.handle_chat_message_use_case import HandleChatMessageUseCase
from app.platform.chat.application.usecase.handle_reply_use_case import HandleReplyUseCase
from app.platform.command.domain.command_handler import CommandHandler
from app.platform.command.domain.command_router import CommandRouter


class PlatformChatClient(ABC):
    def __init__(
        self,
        handle_chat_message_use_case: HandleChatMessageUseCase,
        handle_reply_use_case: HandleReplyUseCase,
        command_router: CommandRouter,
        command_prefix: str,
        help_command_handler: CommandHandler,
        logger: Logger,
    ):
        self._handle_chat_message_use_case = handle_chat_message_use_case
        self._handle_reply_use_case = handle_reply_use_case
        self._command_router = command_router
        self._command_prefix = command_prefix
        self._help_command_handler = help_command_handler
        self.channel_name: str | None = None
        self.bot_name: str | None = None
        self.logger = logger.create_child(__name__)

    def init(self, channel_name: str, bot_name: str, battle_waiting_user: dict[str, str | None]):
        self.channel_name = channel_name
        self.bot_name = bot_name
        self._command_router.apply_bot_name(bot_name, battle_waiting_user)

    async def handle_message(self, user_name: str, message: str):
        if message.startswith(self._command_prefix):
            command_handler = self._command_router.get_command_handler(message)
            if command_handler:
                result = await command_handler.handle(self.channel_name, user_name, message)
                await self.send_channel_message(result)
            else:
                result = await self._help_command_handler.handle(self.channel_name, user_name, message)
                await self.send_channel_message(result)
            return

        if self._is_self_message(user_name):
            return

        chat_message = ChatMessageDTO(
            channel_name=self.channel_name,
            display_name=user_name,
            user_name=user_name.lower(),
            message=message,
            bot_name=self.bot_name,
            occurred_at=datetime.now(UTC),
        )

        if self.is_reply_message(message):
            result = await self._handle_reply_use_case.handle(chat_message)
            await self.send_channel_message(result)
            return

        result = await self._handle_chat_message_use_case.handle(chat_message)

        if result:
            await self.send_channel_message(result)

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
