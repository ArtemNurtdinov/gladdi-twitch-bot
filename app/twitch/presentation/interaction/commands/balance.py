from datetime import datetime
from typing import Any, Awaitable, Callable, ContextManager

from sqlalchemy.orm import Session

from app.twitch.application.interaction.balance.dto import BalanceDTO
from app.twitch.application.interaction.balance.handle_balance_use_case import HandleBalanceUseCase


class BalanceCommandHandler:

    def __init__(
        self,
        handle_balance_use_case: HandleBalanceUseCase,
        db_session_provider: Callable[[], ContextManager[Session]],
        bot_nick_provider: Callable[[], str],
        post_message_fn: Callable[[str, Any], Awaitable[None]],
    ):
        self._handle_balance_use_case = handle_balance_use_case
        self._db_session_provider = db_session_provider
        self.bot_nick_provider = bot_nick_provider
        self.post_message_fn = post_message_fn

    async def handle(self, channel_name: str, display_name: str, ctx):
        user_name = display_name.lower()
        bot_nick = self.bot_nick_provider().lower()

        dto = BalanceDTO(
            channel_name=channel_name,
            display_name=display_name,
            user_name=user_name,
            bot_nick=bot_nick,
            occurred_at=datetime.utcnow(),
        )

        result = await self._handle_balance_use_case.handle(self._db_session_provider, dto)
        await self.post_message_fn(result, ctx)
