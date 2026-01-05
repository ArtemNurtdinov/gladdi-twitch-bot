from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any

from app.commands.ask.application.handle_ask_use_case import HandleAskUseCase
from app.commands.ask.application.model import AskCommandDTO


class AskCommandHandler:
    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        handle_ask_use_case: HandleAskUseCase,
        post_message_fn: Callable[[str, Any], Awaitable[None]],
        bot_nick_provider: Callable[[], str],
    ):
        self.command_prefix = command_prefix
        self.command_name = command_name
        self._handle_ask_use_case = handle_ask_use_case
        self.post_message_fn = post_message_fn
        self.bot_nick_provider = bot_nick_provider

    async def handle(self, channel_name: str, full_message: str, display_name: str, ctx):
        user_message = full_message[len(f"{self.command_prefix}{self.command_name}") :].strip()

        dto = AskCommandDTO(
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            bot_nick=self.bot_nick_provider(),
            occurred_at=datetime.utcnow(),
            message=user_message,
        )

        result = await self._handle_ask_use_case.handle(dto)
        await self.post_message_fn(result, ctx)
