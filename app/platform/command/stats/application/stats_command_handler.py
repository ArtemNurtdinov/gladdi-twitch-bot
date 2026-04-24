from datetime import UTC, datetime

from app.platform.command.domain.command_handler import CommandHandler
from app.platform.command.stats.application.handle_stats_use_case import HandleStatsUseCase
from app.platform.command.stats.application.model import CommandStatsDTO


class StatsCommandHandler(CommandHandler):
    def __init__(self, command_prefix: str, command_name: str, handle_stats_use_case: HandleStatsUseCase):
        self.command_prefix = command_prefix
        self.command_name = command_name
        self._handle_stats_use_case = handle_stats_use_case
        self._bot_name: str | None = None

    def apply_bot_name(self, bot_name) -> None:
        self._bot_name = bot_name

    async def handle(self, channel_name: str, user_name: str, message: str) -> str:
        command_stats = CommandStatsDTO(
            command_prefix=self.command_prefix,
            command_name=self.command_name,
            channel_name=channel_name,
            display_name=user_name,
            user_name=user_name.lower(),
            bot_name=self._bot_name.lower(),
            occurred_at=datetime.now(UTC),
            message=message,
        )

        return await self._handle_stats_use_case.handle(command_stats=command_stats)
