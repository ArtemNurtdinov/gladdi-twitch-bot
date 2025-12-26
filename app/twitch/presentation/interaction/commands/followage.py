from datetime import datetime
from typing import Any, Awaitable, Callable, ContextManager

from sqlalchemy.orm import Session

from app.twitch.application.interaction.follow.dto import FollowageDTO
from app.twitch.application.interaction.follow.handle_followage_use_case import HandleFollowageUseCase


class FollowageCommandHandler:
    def __init__(
        self,
        handle_followage_use_case: HandleFollowageUseCase,
        db_session_provider: Callable[[], ContextManager[Session]],
        bot_nick_provider: Callable[[], str],
        post_message_fn: Callable[[str, Any], Awaitable[None]],
    ):
        self._handle_followage_use_case = handle_followage_use_case
        self._db_session_provider = db_session_provider
        self.bot_nick_provider = bot_nick_provider
        self.post_message_fn = post_message_fn

    async def handle(self, channel_name: str, display_name: str, ctx):
        if not ctx.author:
            return

        dto = FollowageDTO(
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            user_id=str(ctx.author.id),
            bot_nick=self.bot_nick_provider(),
            occurred_at=datetime.utcnow(),
        )

        result = await self._handle_followage_use_case.handle(self._db_session_provider, dto)
        await self.post_message_fn(result, ctx)
