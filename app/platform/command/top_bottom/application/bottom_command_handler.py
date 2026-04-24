from datetime import UTC, datetime

from app.platform.command.domain.command_handler import CommandHandler
from app.platform.command.top_bottom.application.handle_top_bottom_use_case import HandleTopBottomUseCase
from app.platform.command.top_bottom.application.model import BottomDTO


class BottomCommandHandler(CommandHandler):
    _BOTTOM_LIMIT = 5

    def __init__(self, handle_top_bottom_use_case: HandleTopBottomUseCase):
        self._handle_top_bottom_use_case = handle_top_bottom_use_case
        self._bot_name: str | None = None

    def apply_bot_name(self, bot_name) -> None:
        self._bot_name = bot_name

    async def handle(self, channel_name: str, user_name: str, message: str) -> str:
        command_bottom = BottomDTO(
            channel_name=channel_name,
            user_name=user_name.lower(),
            bot_nick=self._bot_name.lower(),
            occurred_at=datetime.now(UTC),
            message=message,
        )

        return await self._handle_top_bottom_use_case.handle_bottom(command_bottom=command_bottom)
