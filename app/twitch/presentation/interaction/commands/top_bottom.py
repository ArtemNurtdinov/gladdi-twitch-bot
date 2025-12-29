from datetime import datetime
from typing import Any, Awaitable, Callable, ContextManager

from sqlalchemy.orm import Session

from app.twitch.application.interaction.top_bottom.model import BottomDTO, TopDTO
from app.twitch.application.interaction.top_bottom.handle_top_bottom_use_case import HandleTopBottomUseCase


class TopBottomCommandHandler:
    _TOP_LIMIT = 7
    _BOTTOM_LIMIT = 10

    def __init__(
        self,
        handle_top_bottom_use_case: HandleTopBottomUseCase,
        db_session_provider: Callable[[], ContextManager[Session]],
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
        command_top: str,
        command_bottom: str,
        bot_nick_provider: Callable[[], str],
        post_message_fn: Callable[[str, Any], Awaitable[None]],
    ):
        self._handle_top_bottom_use_case = handle_top_bottom_use_case
        self._db_session_provider = db_session_provider
        self._db_readonly_session_provider = db_readonly_session_provider
        self.command_top = command_top
        self.command_bottom = command_bottom
        self.bot_nick_provider = bot_nick_provider
        self.post_message_fn = post_message_fn
        self.top_limit = self._TOP_LIMIT
        self.bottom_limit = self._BOTTOM_LIMIT

    async def handle_top(self, channel_name: str, ctx):
        bot_nick = self.bot_nick_provider().lower()

        dto = TopDTO(
            channel_name=channel_name,
            bot_nick=bot_nick,
            occurred_at=datetime.utcnow(),
            limit=self.top_limit,
        )

        result = await self._handle_top_bottom_use_case.handle_top(
            db_readonly_session_provider=self._db_readonly_session_provider,
            db_session_provider=self._db_session_provider,
            command_top=dto
        )

        await self.post_message_fn(result, ctx)

    async def handle_bottom(self, channel_name: str, ctx):
        bot_nick = self.bot_nick_provider().lower()

        dto = BottomDTO(
            channel_name=channel_name,
            bot_nick=bot_nick,
            occurred_at=datetime.utcnow(),
            limit=self.bottom_limit
        )

        result = await self._handle_top_bottom_use_case.handle_bottom(
            db_readonly_session_provider=self._db_readonly_session_provider,
            db_session_provider=self._db_session_provider,
            command_bottom=dto
        )

        await self.post_message_fn(result, ctx)
