from datetime import datetime

from app.platform.command.balance.application.handle_balance_use_case import HandleBalanceUseCase
from app.platform.command.balance.application.model import BalanceDTO
from app.platform.command.domain.command_handler import CommandHandler


class BalanceCommandHandlerImpl(CommandHandler):
    def __init__(self, handle_balance_use_case: HandleBalanceUseCase, bot_name: str):
        self._handle_balance_use_case = handle_balance_use_case
        self._bot_name = bot_name

    async def handle(self, channel_name: str, user_name: str, message: str) -> str:
        balance = BalanceDTO(
            channel_name=channel_name,
            display_name=user_name,
            user_name=user_name.lower(),
            bot_nick=self._bot_name.lower(),
            occurred_at=datetime.utcnow(),
            message=message,
        )

        result = await self._handle_balance_use_case.handle(balance)
        return result
