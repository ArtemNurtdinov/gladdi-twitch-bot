from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.twitch.application.interaction.balance.dto import BalanceDTO
from app.twitch.application.shared.chat_use_case_provider import ChatUseCaseProvider
from app.twitch.application.shared.economy_service_provider import EconomyServiceProvider


class HandleBalanceUseCase:

    def __init__(
        self,
        economy_service_provider: EconomyServiceProvider,
        chat_use_case_provider: ChatUseCaseProvider,
    ):
        self._economy_service_provider = economy_service_provider
        self._chat_use_case_provider = chat_use_case_provider

    async def handle(
        self,
        db_session_provider: Callable[[], ContextManager[Session]],
        dto: BalanceDTO,
    ) -> str:
        with db_session_provider() as db:
            user_balance = self._economy_service_provider.get(db).get_user_balance(
                dto.channel_name,
                dto.user_name,
            )

        result = f"💰 @{dto.display_name}, твой баланс: {user_balance.balance} монет"

        with db_session_provider() as db:
            self._chat_use_case_provider.get(db).save_chat_message(
                channel_name=dto.channel_name,
                user_name=dto.bot_nick,
                content=result,
                current_time=dto.occurred_at,
            )

        return result
