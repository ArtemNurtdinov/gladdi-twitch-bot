from datetime import datetime
from typing import Any, Awaitable, Callable, ContextManager

from sqlalchemy.orm import Session

from app.twitch.application.interaction.top_bottom.dto import BottomDTO, TopDTO
from app.twitch.application.interaction.top_bottom.handle_top_bottom_use_case import HandleTopBottomUseCase


class TopBottomCommandHandler:

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

    async def handle_top(self, channel_name: str, ctx):
        bot_nick = self.bot_nick_provider().lower()

        dto = TopDTO(
            channel_name=channel_name,
            display_name="",
            user_name="",
            bot_nick=bot_nick,
            occurred_at=datetime.utcnow(),
            limit=7,
        )

        result = await self._handle_top_bottom_use_case.handle_top(
            db_readonly_session_provider=self._db_readonly_session_provider,
            db_session_provider=self._db_session_provider,
            dto=dto,
        )

        await self.post_message_fn(result, ctx)

    async def handle_bottom(self, channel_name: str, ctx):
        bot_nick = self.bot_nick_provider().lower()

        dto = BottomDTO(
            channel_name=channel_name,
            display_name="",
            user_name="",
            bot_nick=bot_nick,
            occurred_at=datetime.utcnow(),
            limit=10,
        )

        result = await self._handle_top_bottom_use_case.handle_bottom(
            db_readonly_session_provider=self._db_readonly_session_provider,
            db_session_provider=self._db_session_provider,
            dto=dto,
        )

        await self.post_message_fn(result, ctx)
