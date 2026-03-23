from datetime import datetime

from app.platform.command.balance.application.handle_balance_use_case import HandleBalanceUseCase
from app.platform.command.balance.application.model import BalanceDTO
from app.platform.command.domain.command_handler import CommandHandler


class BalanceCommandHandlerImpl(CommandHandler):
    def __init__(self, command_prefix: str, command_name: str, handle_balance_use_case: HandleBalanceUseCase, bot_name: str):
        self._command_prefix = command_prefix
        self._command_name = command_name
        self._handle_balance_use_case = handle_balance_use_case
        self._bot_name = bot_name

    async def handle(self, channel_name: str, user_name: str, message: str) -> str:
        balance = BalanceDTO(
            command_prefix=self._command_prefix,
            command_name=self._command_name,
            channel_name=channel_name,
            display_name=user_name,
            user_name=user_name.lower(),
            bot_nick=self._bot_name.lower(),
            occurred_at=datetime.utcnow(),
        )

        result = await self._handle_balance_use_case.handle(balance)
        return result
