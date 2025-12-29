from datetime import datetime
from typing import Any, Awaitable, Callable, ContextManager

from sqlalchemy.orm import Session

from app.twitch.application.interaction.help.model import HelpDTO
from app.twitch.application.interaction.help.handle_help_use_case import HandleHelpUseCase


class HelpCommandHandler:

    def __init__(
        self,
        command_prefix: str,
        handle_help_use_case: HandleHelpUseCase,
        db_session_provider: Callable[[], ContextManager[Session]],
        commands: set[str],
        bot_nick_provider: Callable[[], str],
        post_message_fn: Callable[[str, Any], Awaitable[None]]
    ):
        self.command_prefix = command_prefix
        self._handle_help_use_case = handle_help_use_case
        self._db_session_provider = db_session_provider
        self.commands = commands
        self.bot_nick_provider = bot_nick_provider
        self.post_message_fn = post_message_fn

    async def handle(self, channel_name: str, ctx):
        bot_nick = self.bot_nick_provider().lower()

        dto = HelpDTO(
            command_prefix=self.command_prefix,
            channel_name=channel_name,
            bot_nick=bot_nick,
            occurred_at=datetime.utcnow(),
            commands=self.commands,
        )

        result = await self._handle_help_use_case.handle(self._db_session_provider, dto)

        await self.post_message_fn(result, ctx)
