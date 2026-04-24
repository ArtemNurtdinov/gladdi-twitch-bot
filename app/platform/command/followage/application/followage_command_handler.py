from datetime import UTC, datetime

from app.platform.command.domain.command_handler import CommandHandler
from app.platform.command.followage.application.model import FollowageDTO
from app.platform.command.followage.application.usecase.handle_followage_use_case import HandleFollowAgeUseCase


class FollowageCommandHandler(CommandHandler):
    def __init__(self, command_prefix: str, command_name: str, handle_follow_age_use_case: HandleFollowAgeUseCase):
        self._command_prefix = command_prefix
        self._command_name = command_name
        self._handle_follow_age_use_case = handle_follow_age_use_case
        self._bot_name: str | None = None

    def apply_bot_name(self, bot_name) -> None:
        self._bot_name = bot_name

    async def handle(self, channel_name: str, user_name: str, message: str) -> str:
        followage = FollowageDTO(
            channel_name=channel_name,
            display_name=user_name,
            user_name=user_name.lower(),
            bot_nick=self._bot_name,
            occurred_at=datetime.now(UTC),
            message=message,
        )
        return await self._handle_follow_age_use_case.handle(followage)
