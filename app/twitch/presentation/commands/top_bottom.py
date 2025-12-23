from datetime import datetime
from typing import Callable, Any, Awaitable

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from app.economy.domain.economy_service import EconomyService
from core.db import SessionLocal, db_ro_session


class TopBottomCommandHandler:

    def __init__(
        self,
        economy_service_factory: Callable[[Session], EconomyService],
        chat_use_case_factory: Callable[[Session], ChatUseCase],
        command_top: str,
        command_bottom: str,
        bot_nick_provider: Callable[[], str],
        post_message_fn: Callable[[str, Any], Awaitable[None]],
    ):
        self._economy_service = economy_service_factory
        self._chat_use_case = chat_use_case_factory
        self.command_top = command_top
        self.command_bottom = command_bottom
        self.bot_nick_provider = bot_nick_provider
        self.post_message_fn = post_message_fn

    async def handle_top(self, channel_name: str, ctx):
        bot_nick = self.bot_nick_provider().lower()

        with db_ro_session() as db:
            top_users = self._economy_service(db).get_top_users(channel_name, limit=7)

        if not top_users:
            result = "Нет данных для отображения топа."
        else:
            result = "ТОП БОГАЧЕЙ:\n"
            for i, user in enumerate(top_users, 1):
                result += f"{i}. {user.user_name}: {user.balance} монет."

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, bot_nick, result, datetime.utcnow())

        await self.post_message_fn(result, ctx)

    async def handle_bottom(self, channel_name: str, ctx):
        bot_nick = self.bot_nick_provider().lower()

        with db_ro_session() as db:
            bottom_users = self._economy_service(db).get_bottom_users(channel_name, limit=10)

        if not bottom_users:
            result = "Нет данных для отображения бомжей."
        else:
            result = "💸 ТОП БОМЖЕЙ:\n"
            for i, user in enumerate(bottom_users, 1):
                result += f"{i}. {user.user_name}: {user.balance} монет."

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, bot_nick, result, datetime.utcnow())

        await self.post_message_fn(result, ctx)
