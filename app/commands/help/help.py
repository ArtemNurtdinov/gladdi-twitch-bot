from collections.abc import Awaitable, Callable
from contextlib import AbstractContextManager
from datetime import datetime

from sqlalchemy.orm import Session

from app.commands.help.handle_help_use_case import HandleHelpUseCase
from app.commands.help.model import HelpDTO
from core.chat.interfaces import ChatContext


class HelpCommandHandler:
    def __init__(
        self,
        command_prefix: str,
        handle_help_use_case: HandleHelpUseCase,
        db_session_provider: Callable[[], AbstractContextManager[Session]],
        commands: set[str],
        bot_nick: str,
        post_message_fn: Callable[[str, ChatContext], Awaitable[None]],
    ):
        self.command_prefix = command_prefix
        self._handle_help_use_case = handle_help_use_case
        self._db_session_provider = db_session_provider
        self.commands = commands
        self._bot_nick = bot_nick
        self.post_message_fn = post_message_fn

    async def handle(self, channel_name: str, chat_ctx: ChatContext):
        bot_nick = self._bot_nick.lower()

        dto = HelpDTO(
            command_prefix=self.command_prefix,
            channel_name=channel_name,
            bot_nick=bot_nick,
            occurred_at=datetime.utcnow(),
            commands=self.commands,
        )

        result = await self._handle_help_use_case.handle(self._db_session_provider, dto)

        await self.post_message_fn(result, chat_ctx)
