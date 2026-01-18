from collections.abc import Awaitable, Callable
from datetime import datetime

from app.commands.top_bottom.application.handle_top_bottom_use_case import HandleTopBottomUseCase
from app.commands.top_bottom.application.model import BottomDTO, TopDTO
from core.chat.interfaces import ChatContext


class TopBottomCommandHandler:
    _TOP_LIMIT = 7
    _BOTTOM_LIMIT = 10

    def __init__(
        self,
        command_prefix: str,
        command_top: str,
        command_bottom: str,
        handle_top_bottom_use_case: HandleTopBottomUseCase,
        bot_nick: str,
        post_message_fn: Callable[[str, ChatContext], Awaitable[None]],
    ):
        self.command_prefix = command_prefix
        self.command_top = command_top
        self.command_bottom = command_bottom
        self._handle_top_bottom_use_case = handle_top_bottom_use_case
        self._bot_nick = bot_nick
        self.post_message_fn = post_message_fn
        self.top_limit = self._TOP_LIMIT
        self.bottom_limit = self._BOTTOM_LIMIT

    async def handle_top(self, channel_name: str, display_name: str, chat_ctx: ChatContext):
        bot_nick = self._bot_nick.lower()

        dto = TopDTO(
            command_prefix=self.command_prefix,
            command_name=self.command_top,
            channel_name=channel_name,
            user_name=display_name.lower(),
            bot_nick=bot_nick,
            occurred_at=datetime.utcnow(),
            limit=self.top_limit,
        )

        result = await self._handle_top_bottom_use_case.handle_top(
            command_top=dto
        )

        await self.post_message_fn(result, chat_ctx)

    async def handle_bottom(self, channel_name: str, display_name: str, chat_ctx: ChatContext):
        bot_nick = self._bot_nick.lower()

        dto = BottomDTO(
            command_prefix=self.command_prefix,
            command_name=self.command_bottom,
            channel_name=channel_name,
            user_name=display_name.lower(),
            bot_nick=bot_nick,
            occurred_at=datetime.utcnow(),
            limit=self.bottom_limit,
        )

        result = await self._handle_top_bottom_use_case.handle_bottom(
            command_bottom=dto,
        )

        await self.post_message_fn(result, chat_ctx)
