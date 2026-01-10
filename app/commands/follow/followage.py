from collections.abc import Awaitable, Callable
from datetime import datetime

from app.commands.follow.application.handle_followage_use_case import HandleFollowAgeUseCase
from app.commands.follow.application.model import FollowageDTO
from core.chat.interfaces import ChatContext


class FollowageCommandHandler:
    def __init__(
        self,
        handle_follow_age_use_case: HandleFollowAgeUseCase,
        bot_nick_provider: Callable[[], str],
        post_message_fn: Callable[[str, ChatContext], Awaitable[None]],
    ):
        self._handle_follow_age_use_case = handle_follow_age_use_case
        self.bot_nick_provider = bot_nick_provider
        self.post_message_fn = post_message_fn

    async def handle(self, channel_name: str, display_name: str, chat_ctx: ChatContext):
        user_id = chat_ctx.author_id
        if not user_id:
            return

        dto = FollowageDTO(
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            bot_nick=self.bot_nick_provider(),
            occurred_at=datetime.utcnow(),
            user_id=str(user_id),
        )

        result = await self._handle_follow_age_use_case.handle(dto)
        if result:
            await self.post_message_fn(result, chat_ctx)
