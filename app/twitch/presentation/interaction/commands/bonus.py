from collections.abc import Awaitable, Callable
from contextlib import AbstractContextManager
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.commands.bonus.handle_bonus_use_case import HandleBonusUseCase
from app.commands.bonus.model import BonusDTO


class BonusCommandHandler:
    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        handle_bonus_use_case: HandleBonusUseCase,
        db_session_provider: Callable[[], AbstractContextManager[Session]],
        db_readonly_session_provider: Callable[[], AbstractContextManager[Session]],
        bot_nick_provider: Callable[[], str],
        post_message_fn: Callable[[str, Any], Awaitable[None]],
    ):
        self.command_prefix = command_prefix
        self.command_name = command_name
        self._handle_bonus_use_case = handle_bonus_use_case
        self._db_session_provider = db_session_provider
        self._db_readonly_session_provider = db_readonly_session_provider
        self.bot_nick_provider = bot_nick_provider
        self.post_message_fn = post_message_fn

    async def handle(self, channel_name: str, display_name: str, ctx):
        bot_nick = self.bot_nick_provider().lower()

        bonus = BonusDTO(
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            bot_nick=bot_nick,
            occurred_at=datetime.utcnow(),
        )

        result = await self._handle_bonus_use_case.handle(
            db_session_provider=self._db_session_provider,
            db_readonly_session_provider=self._db_readonly_session_provider,
            chat_context_dto=bonus,
        )

        await self.post_message_fn(result, ctx)
