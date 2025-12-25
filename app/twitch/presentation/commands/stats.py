from datetime import datetime
from typing import Any, Awaitable, Callable, ContextManager

from sqlalchemy.orm import Session

from app.twitch.application.stats.dto import StatsDTO
from app.twitch.application.stats.handle_stats_use_case import HandleStatsUseCase


class StatsCommandHandler:

    def __init__(
        self,
        handle_stats_use_case: HandleStatsUseCase,
        db_session_provider: Callable[[], ContextManager[Session]],
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
        command_name: str,
        bot_nick_provider: Callable[[], str],
        post_message_fn: Callable[[str, Any], Awaitable[None]],
    ):
        self._handle_stats_use_case = handle_stats_use_case
        self._db_session_provider = db_session_provider
        self._db_readonly_session_provider = db_readonly_session_provider
        self.command_name = command_name
        self.bot_nick_provider = bot_nick_provider
        self.post_message_fn = post_message_fn

    async def handle(self, channel_name: str, display_name: str, ctx):
        dto = StatsDTO(
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            bot_nick=self.bot_nick_provider().lower(),
            occurred_at=datetime.utcnow(),
        )

        result = await self._handle_stats_use_case.handle(
            db_session_provider=self._db_session_provider,
            db_readonly_session_provider=self._db_readonly_session_provider,
            dto=dto,
        )

        await self.post_message_fn(result, ctx)
