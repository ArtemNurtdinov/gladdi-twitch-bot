from collections.abc import Awaitable, Callable
from datetime import datetime

from app.commands.stats.application.handle_stats_use_case import HandleStatsUseCase
from app.commands.stats.application.model import CommandStatsDTO
from app.commands.stats.application.stats_command_handler import StatsCommandHandler


class StatsCommandHandlerImpl(StatsCommandHandler):
    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        handle_stats_use_case: HandleStatsUseCase,
        bot_name: str,
        post_message_fn: Callable[[str], Awaitable[None]],
    ):
        self.command_prefix = command_prefix
        self.command_name = command_name
        self._handle_stats_use_case = handle_stats_use_case
        self._bot_name = bot_name
        self._post_message_fn = post_message_fn

    async def handle(self, channel_name: str, display_name: str):
        command_stats = CommandStatsDTO(
            command_prefix=self.command_prefix,
            command_name=self.command_name,
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            bot_name=self._bot_name.lower(),
            occurred_at=datetime.utcnow(),
        )

        result = await self._handle_stats_use_case.handle(command_stats=command_stats)

        await self._post_message_fn(result)
