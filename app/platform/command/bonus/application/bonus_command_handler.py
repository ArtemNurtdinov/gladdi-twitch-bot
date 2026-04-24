from datetime import UTC, datetime

from app.platform.command.bonus.application.handle_bonus_use_case import HandleBonusUseCase
from app.platform.command.bonus.application.model import BonusDTO
from app.platform.command.domain.command_handler import CommandHandler


class BonusCommandHandler(CommandHandler):
    def __init__(self, handle_bonus_use_case: HandleBonusUseCase):
        self._handle_bonus_use_case = handle_bonus_use_case
        self._bot_name: str | None = None

    def apply_bot_name(self, bot_name) -> None:
        self._bot_name = bot_name

    async def handle(self, channel_name: str, user_name: str, message: str) -> str:
        bonus = BonusDTO(
            channel_name=channel_name,
            display_name=user_name,
            user_name=user_name.lower(),
            bot_name=self._bot_name.lower(),
            occurred_at=datetime.now(UTC),
            message=message,
        )

        return await self._handle_bonus_use_case.handle(bonus=bonus)
