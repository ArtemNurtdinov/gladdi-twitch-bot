from datetime import datetime
from typing import Any, Awaitable, Callable, ContextManager

from sqlalchemy.orm import Session

from app.twitch.application.interaction.ask.dto import AskCommandDTO
from app.twitch.application.interaction.ask.handle_ask_use_case import HandleAskUseCase


class AskCommandHandler:

    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        handle_ask_use_case: HandleAskUseCase,
        db_session_provider: Callable[[], ContextManager[Session]],
        post_message_fn: Callable[[str, Any], Awaitable[None]],
        bot_nick_provider: Callable[[], str],
    ):
        self.command_prefix = command_prefix
        self.command_name = command_name
        self._handle_ask_use_case = handle_ask_use_case
        self._db_session_provider = db_session_provider
        self.post_message_fn = post_message_fn
        self.bot_nick_provider = bot_nick_provider

    async def handle(self, channel_name: str, full_message: str, display_name: str, ctx):
        user_message = full_message[len(f"{self.command_prefix}{self.command_name}"):].strip()

        dto = AskCommandDTO(
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            message=user_message,
            bot_nick=self.bot_nick_provider(),
            occurred_at=datetime.utcnow(),
        )

        result = await self._handle_ask_use_case.handle(self._db_session_provider, dto)
        await self.post_message_fn(result, ctx)
