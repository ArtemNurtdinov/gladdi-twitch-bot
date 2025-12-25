from datetime import datetime
from typing import Any, Awaitable, Callable, ContextManager

from sqlalchemy.orm import Session

from app.twitch.application.rps.dto import RpsDTO
from app.twitch.application.rps.handle_rps_use_case import HandleRpsUseCase


class RpsCommandHandler:

    def __init__(
        self,
        handle_rps_use_case: HandleRpsUseCase,
        db_session_provider: Callable[[], ContextManager[Session]],
        bot_nick_provider: Callable[[], str],
        post_message_fn: Callable[[str, Any], Awaitable[None]],
    ):
        self._handle_rps_use_case = handle_rps_use_case
        self._db_session_provider = db_session_provider
        self.bot_nick_provider = bot_nick_provider
        self.post_message_fn = post_message_fn

    async def handle(self, channel_name: str, display_name: str, ctx, choice: str | None):
        dto = RpsDTO(
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            bot_nick=self.bot_nick_provider().lower(),
            occurred_at=datetime.utcnow(),
            choice_input=choice,
        )

        result = await self._handle_rps_use_case.handle(
            db_session_provider=self._db_session_provider,
            dto=dto,
        )

        await self.post_message_fn(result, ctx)
