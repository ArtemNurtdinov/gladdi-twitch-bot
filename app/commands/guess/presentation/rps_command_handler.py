from collections.abc import Awaitable, Callable
from datetime import datetime

from app.minigame.application.handle_rps_use_case import HandleRpsUseCase
from app.minigame.application.model import RpsDTO
from core.chat.interfaces import ChatContext


class RpsCommandHandler:
    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        handle_rps_use_case: HandleRpsUseCase,
        bot_nick: str,
        post_message_fn: Callable[[str, ChatContext], Awaitable[None]],
    ):
        self._command_prefix = command_prefix
        self._command_name = command_name
        self._handle_rps_use_case = handle_rps_use_case
        self._bot_nick = bot_nick
        self.post_message_fn = post_message_fn

    async def handle(self, channel_name: str, display_name: str, chat_ctx: ChatContext, choice: str | None):
        dto = RpsDTO(
            command_prefix=self._command_prefix,
            command_name=self._command_name,
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            bot_nick=self._bot_nick.lower(),
            occurred_at=datetime.utcnow(),
            choice_input=choice,
        )

        result = await self._handle_rps_use_case.handle(dto=dto)

        await self.post_message_fn(result, chat_ctx)
