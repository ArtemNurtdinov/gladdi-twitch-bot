from collections.abc import Awaitable, Callable
from datetime import datetime

from app.commands.balance.application.handle_balance_use_case import HandleBalanceUseCase
from app.commands.balance.application.model import BalanceDTO
from app.platform.command.domain.command_handler import CommandHandler


class BalanceCommandHandlerImpl(CommandHandler):
    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        handle_balance_use_case: HandleBalanceUseCase,
        bot_name: str,
        post_message_fn: Callable[[str], Awaitable[None]],
    ):
        self._command_prefix = command_prefix
        self._command_name = command_name
        self._handle_balance_use_case = handle_balance_use_case
        self._bot_name = bot_name
        self.post_message_fn = post_message_fn

    async def handle_command(self, channel_name: str, user_name: str, user_message: str):
        dto = BalanceDTO(
            command_prefix=self._command_prefix,
            command_name=self._command_name,
            channel_name=channel_name,
            display_name=user_name,
            user_name=user_name.lower(),
            bot_nick=self._bot_name.lower(),
            occurred_at=datetime.utcnow(),
        )

        result = await self._handle_balance_use_case.handle(dto)
        await self.post_message_fn(result)
