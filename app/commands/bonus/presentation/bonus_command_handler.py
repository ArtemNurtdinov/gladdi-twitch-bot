from collections.abc import Awaitable, Callable
from datetime import datetime

from app.commands.bonus.application.handle_bonus_use_case import HandleBonusUseCase
from app.commands.bonus.application.model import BonusDTO
from core.chat.interfaces import ChatContext


class BonusCommandHandler:
    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        handle_bonus_use_case: HandleBonusUseCase,
        bot_nick: str,
        post_message_fn: Callable[[str, ChatContext], Awaitable[None]],
    ):
        self.command_prefix = command_prefix
        self.command_name = command_name
        self._handle_bonus_use_case = handle_bonus_use_case
        self._bot_nick = bot_nick
        self.post_message_fn = post_message_fn

    async def handle(self, channel_name: str, display_name: str, chat_ctx: ChatContext):
        bot_nick = self._bot_nick.lower()

        bonus = BonusDTO(
            command_prefix=self.command_prefix,
            command_name=self.command_name,
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            bot_nick=bot_nick,
            occurred_at=datetime.utcnow(),
        )

        result = await self._handle_bonus_use_case.handle(chat_context_dto=bonus)

        await self.post_message_fn(result, chat_ctx)
