import logging
from datetime import datetime
from typing import Callable

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from app.economy.domain.economy_service import EconomyService
from core.db import SessionLocal

logger = logging.getLogger(__name__)


class BalanceCommandHandler:

    def __init__(
        self,
        economy_service_factory: Callable[[Session], EconomyService],
        chat_use_case_factory: Callable[[Session], ChatUseCase],
        nick_provider: Callable[[], str],
    ):
        self._economy_service = economy_service_factory
        self._chat_use_case = chat_use_case_factory
        self.nick_provider = nick_provider

    async def handle(self, channel_name: str, display_name: str, ctx):
        user_name = display_name.lower()
        bot_nick = self.nick_provider() or ""

        with SessionLocal.begin() as db:
            user_balance = self._economy_service(db).get_user_balance(channel_name, user_name)

        result = f"💰 @{display_name}, твой баланс: {user_balance.balance} монет"

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())
        await ctx.send(result)

