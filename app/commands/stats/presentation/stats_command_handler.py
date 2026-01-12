from collections.abc import Awaitable, Callable
from contextlib import AbstractContextManager
from datetime import datetime

from sqlalchemy.orm import Session

from app.commands.stats.application.handle_stats_use_case import HandleStatsUseCase
from app.commands.stats.application.model import StatsDTO
from core.chat.interfaces import ChatContext


class StatsCommandHandler:
    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        handle_stats_use_case: HandleStatsUseCase,
        db_session_provider: Callable[[], AbstractContextManager[Session]],
        db_readonly_session_provider: Callable[[], AbstractContextManager[Session]],
        bot_nick: str,
        post_message_fn: Callable[[str, ChatContext], Awaitable[None]],
    ):
        self.command_prefix = command_prefix
        self.command_name = command_name
        self._handle_stats_use_case = handle_stats_use_case
        self._db_session_provider = db_session_provider
        self._db_readonly_session_provider = db_readonly_session_provider
        self._bot_nick = bot_nick
        self.post_message_fn = post_message_fn

    async def handle(self, channel_name: str, display_name: str, chat_ctx: ChatContext):
        dto = StatsDTO(
            command_prefix=self.command_prefix,
            command_name=self.command_name,
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            bot_nick=self._bot_nick.lower(),
            occurred_at=datetime.utcnow(),
        )

        result = await self._handle_stats_use_case.handle(
            db_session_provider=self._db_session_provider,
            db_readonly_session_provider=self._db_readonly_session_provider,
            command_stats=dto,
        )

        await self.post_message_fn(result, chat_ctx)
