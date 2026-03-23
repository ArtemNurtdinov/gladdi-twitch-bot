from datetime import datetime

from app.platform.command.bonus.application.handle_bonus_use_case import HandleBonusUseCase
from app.platform.command.bonus.application.model import BonusDTO
from app.platform.command.domain.command_handler import CommandHandler


class BonusCommandHandlerImpl(CommandHandler):
    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        handle_bonus_use_case: HandleBonusUseCase,
        bot_name: str,
    ):
        self.command_prefix = command_prefix
        self.command_name = command_name
        self._handle_bonus_use_case = handle_bonus_use_case
        self._bot_name = bot_name

    async def handle(self, channel_name: str, user_name: str, message: str) -> str:
        bonus = BonusDTO(
            channel_name=channel_name,
            display_name=user_name,
            user_name=user_name.lower(),
            bot_name=self._bot_name.lower(),
            occurred_at=datetime.utcnow(),
            message=message,
        )

        return await self._handle_bonus_use_case.handle(bonus=bonus)
