from collections.abc import Awaitable, Callable
from datetime import datetime

from app.commands.bonus.application.bonus_command_handler import BonusCommandHandler
from app.commands.bonus.application.handle_bonus_use_case import HandleBonusUseCase
from app.commands.bonus.application.model import BonusDTO


class BonusCommandHandlerImpl(BonusCommandHandler):
    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        handle_bonus_use_case: HandleBonusUseCase,
        bot_name: str,
        post_message_fn: Callable[[str], Awaitable[None]],
    ):
        self.command_prefix = command_prefix
        self.command_name = command_name
        self._handle_bonus_use_case = handle_bonus_use_case
        self._bot_name = bot_name
        self.post_message_fn = post_message_fn

    async def handle(self, channel_name: str, display_name: str):
        bonus = BonusDTO(
            command_prefix=self.command_prefix,
            command_name=self.command_name,
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            bot_nick=self._bot_name.lower(),
            occurred_at=datetime.utcnow(),
        )

        result = await self._handle_bonus_use_case.handle(bonus=bonus)

        await self.post_message_fn(result)
