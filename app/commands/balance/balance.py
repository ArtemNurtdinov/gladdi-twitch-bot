from collections.abc import Awaitable, Callable
from contextlib import AbstractContextManager
from datetime import datetime

from sqlalchemy.orm import Session

from app.commands.balance.handle_balance_use_case import HandleBalanceUseCase
from app.commands.balance.model import BalanceDTO
from core.chat.interfaces import ChatContext


class BalanceCommandHandler:
    def __init__(
        self,
        handle_balance_use_case: HandleBalanceUseCase,
        db_session_provider: Callable[[], AbstractContextManager[Session]],
        bot_nick: str,
        post_message_fn: Callable[[str, ChatContext], Awaitable[None]],
    ):
        self._handle_balance_use_case = handle_balance_use_case
        self._db_session_provider = db_session_provider
        self._bot_nick = bot_nick
        self.post_message_fn = post_message_fn

    async def handle(self, channel_name: str, display_name: str, chat_ctx: ChatContext):
        user_name = display_name.lower()
        bot_nick = self._bot_nick.lower()

        dto = BalanceDTO(
            channel_name=channel_name,
            display_name=display_name,
            user_name=user_name,
            bot_nick=bot_nick,
            occurred_at=datetime.utcnow(),
        )

        result = await self._handle_balance_use_case.handle(self._db_session_provider, dto)
        await self.post_message_fn(result, chat_ctx)
