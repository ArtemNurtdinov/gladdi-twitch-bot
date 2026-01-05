from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any

from app.commands.follow.application.handle_followage_use_case import HandleFollowAgeUseCase
from app.commands.follow.application.model import FollowageDTO


class FollowageCommandHandler:
    def __init__(
        self,
        handle_follow_age_use_case: HandleFollowAgeUseCase,
        bot_nick_provider: Callable[[], str],
        post_message_fn: Callable[[str, Any], Awaitable[None]],
    ):
        self._handle_follow_age_use_case = handle_follow_age_use_case
        self.bot_nick_provider = bot_nick_provider
        self.post_message_fn = post_message_fn

    async def handle(self, channel_name: str, display_name: str, ctx):
        if not ctx.author:
            return

        dto = FollowageDTO(
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            bot_nick=self.bot_nick_provider(),
            occurred_at=datetime.utcnow(),
            user_id=str(ctx.author.id),
        )

        result = await self._handle_follow_age_use_case.handle(dto)
        if result:
            await self.post_message_fn(result, ctx)
