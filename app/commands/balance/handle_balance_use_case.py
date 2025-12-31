from collections.abc import Callable
from contextlib import AbstractContextManager

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from app.commands.balance.model import BalanceDTO
from app.economy.domain.economy_service import EconomyService
from core.provider import Provider


class HandleBalanceUseCase:
    def __init__(
        self,
        economy_service_provider: Provider[EconomyService],
        chat_use_case_provider: Provider[ChatUseCase],
    ):
        self._economy_service_provider = economy_service_provider
        self._chat_use_case_provider = chat_use_case_provider

    async def handle(
        self,
        db_session_provider: Callable[[], AbstractContextManager[Session]],
        command_balance_dto: BalanceDTO,
    ) -> str:
        with db_session_provider() as db:
            user_balance = self._economy_service_provider.get(db).get_user_balance(
                channel_name=command_balance_dto.channel_name,
                user_name=command_balance_dto.user_name,
            )

        result = f"💰 @{command_balance_dto.display_name}, твой баланс: {user_balance.balance} монет"

        with db_session_provider() as db:
            self._chat_use_case_provider.get(db).save_chat_message(
                channel_name=command_balance_dto.channel_name,
                user_name=command_balance_dto.bot_nick,
                content=result,
                current_time=command_balance_dto.occurred_at,
            )

        return result
