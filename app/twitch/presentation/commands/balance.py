import logging
from datetime import datetime
from typing import Callable

from core.db import SessionLocal

logger = logging.getLogger(__name__)


class BalanceCommandHandler:

    def __init__(
        self,
        economy_service_factory,
        chat_use_case_factory,
        command_name: str,
        nick_provider: Callable[[], str],
    ):
        self._economy_service = economy_service_factory
        self._chat_use_case = chat_use_case_factory
        self.command_name = command_name
        self.nick_provider = nick_provider

    async def handle(self, ctx):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name
        bot_nick = self.nick_provider() or ""

        logger.info(f"Команда {self.command_name} от пользователя {user_name}")

        with SessionLocal.begin() as db:
            user_balance = self._economy_service(db).get_user_balance(channel_name, user_name)

        result = f"💰 @{user_name}, твой баланс: {user_balance.balance} монет"

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())
        await ctx.send(result)

