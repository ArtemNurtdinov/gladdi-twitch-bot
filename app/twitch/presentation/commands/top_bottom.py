import asyncio
import logging
from datetime import datetime
from typing import Callable

from core.db import SessionLocal, db_ro_session

logger = logging.getLogger(__name__)


class TopBottomCommandHandler:
    """Обработчик топов богачей и бомжей."""

    def __init__(
        self,
        economy_service_factory,
        chat_use_case_factory,
        command_top: str,
        command_bottom: str,
        nick_provider: Callable[[], str],
        split_text_fn: Callable[[str], list[str]],
    ):
        self._economy_service = economy_service_factory
        self._chat_use_case = chat_use_case_factory
        self.command_top = command_top
        self.command_bottom = command_bottom
        self.nick_provider = nick_provider
        self.split_text = split_text_fn

    async def handle_top(self, ctx):
        channel_name = ctx.channel.name
        bot_nick = self.nick_provider() or ""

        logger.info(f"Команда {self.command_top}")

        with db_ro_session() as db:
            top_users = self._economy_service(db).get_top_users(channel_name, limit=7)

        if not top_users:
            result = "Нет данных для отображения топа."
        else:
            result = "ТОП БОГАЧЕЙ:\n"
            for i, user in enumerate(top_users, 1):
                result += f"{i}. {user.user_name}: {user.balance} монет."

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())

        messages = self.split_text(result)
        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)

    async def handle_bottom(self, ctx):
        channel_name = ctx.channel.name
        bot_nick = self.nick_provider() or ""

        logger.info(f"Команда {self.command_bottom}")

        with db_ro_session() as db:
            bottom_users = self._economy_service(db).get_bottom_users(channel_name, limit=10)

        if not bottom_users:
            result = "Нет данных для отображения бомжей."
        else:
            result = "💸 ТОП БОМЖЕЙ:\n"
            for i, user in enumerate(bottom_users, 1):
                result += f"{i}. {user.user_name}: {user.balance} монет."

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())

        messages = self.split_text(result)
        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)

