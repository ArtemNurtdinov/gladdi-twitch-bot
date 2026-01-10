from collections.abc import Awaitable, Callable
from contextlib import AbstractContextManager
from datetime import datetime

from sqlalchemy.orm import Session

from app.commands.top_bottom.handle_top_bottom_use_case import HandleTopBottomUseCase
from app.commands.top_bottom.model import BottomDTO, TopDTO
from core.chat.interfaces import ChatContext


class TopBottomCommandHandler:
    _TOP_LIMIT = 7
    _BOTTOM_LIMIT = 10

    def __init__(
        self,
        handle_top_bottom_use_case: HandleTopBottomUseCase,
        db_session_provider: Callable[[], AbstractContextManager[Session]],
        db_readonly_session_provider: Callable[[], AbstractContextManager[Session]],
        command_top: str,
        command_bottom: str,
        bot_nick: str,
        post_message_fn: Callable[[str, ChatContext], Awaitable[None]],
    ):
        self._handle_top_bottom_use_case = handle_top_bottom_use_case
        self._db_session_provider = db_session_provider
        self._db_readonly_session_provider = db_readonly_session_provider
        self.command_top = command_top
        self.command_bottom = command_bottom
        self._bot_nick = bot_nick
        self.post_message_fn = post_message_fn
        self.top_limit = self._TOP_LIMIT
        self.bottom_limit = self._BOTTOM_LIMIT

    async def handle_top(self, channel_name: str, chat_ctx: ChatContext):
        bot_nick = self._bot_nick.lower()

        dto = TopDTO(
            channel_name=channel_name,
            bot_nick=bot_nick,
            occurred_at=datetime.utcnow(),
            limit=self.top_limit,
        )

        result = await self._handle_top_bottom_use_case.handle_top(
            db_readonly_session_provider=self._db_readonly_session_provider, db_session_provider=self._db_session_provider, command_top=dto
        )

        await self.post_message_fn(result, chat_ctx)

    async def handle_bottom(self, channel_name: str, chat_ctx: ChatContext):
        bot_nick = self._bot_nick.lower()

        dto = BottomDTO(channel_name=channel_name, bot_nick=bot_nick, occurred_at=datetime.utcnow(), limit=self.bottom_limit)

        result = await self._handle_top_bottom_use_case.handle_bottom(
            db_readonly_session_provider=self._db_readonly_session_provider,
            db_session_provider=self._db_session_provider,
            command_bottom=dto,
        )

        await self.post_message_fn(result, chat_ctx)
