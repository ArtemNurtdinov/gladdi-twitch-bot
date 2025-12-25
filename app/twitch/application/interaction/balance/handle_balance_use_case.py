from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from app.economy.domain.economy_service import EconomyService
from app.twitch.application.interaction.balance.dto import BalanceDTO


class HandleBalanceUseCase:

    def __init__(
        self,
        economy_service_factory: Callable[[Session], EconomyService],
        chat_use_case_factory: Callable[[Session], ChatUseCase],
    ):
        self._economy_service_factory = economy_service_factory
        self._chat_use_case_factory = chat_use_case_factory

    async def handle(
        self,
        db_session_provider: Callable[[], ContextManager[Session]],
        dto: BalanceDTO,
    ) -> str:
        with db_session_provider() as db:
            user_balance = self._economy_service_factory(db).get_user_balance(
                dto.channel_name,
                dto.user_name,
            )

        result = f"💰 @{dto.display_name}, твой баланс: {user_balance.balance} монет"

        with db_session_provider() as db:
            self._chat_use_case_factory(db).save_chat_message(
                channel_name=dto.channel_name,
                user_name=dto.bot_nick,
                content=result,
                current_time=dto.occurred_at,
            )

        return result

