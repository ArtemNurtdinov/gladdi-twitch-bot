from datetime import UTC, datetime

from app.platform.command.domain.command_handler import CommandHandler
from app.platform.command.help.application.handle_help_use_case import HandleHelpUseCase
from app.platform.command.help.application.model import HelpDTO


class HelpCommandHandler(CommandHandler):
    def __init__(
        self,
        command_prefix: str,
        handle_help_use_case: HandleHelpUseCase,
        commands: set[str],
    ):
        self.command_prefix = command_prefix
        self._handle_help_use_case = handle_help_use_case
        self.commands = commands
        self._bot_name: str | None = None

    def apply_bot_name(self, bot_name) -> None:
        self._bot_name = bot_name

    async def handle(self, channel_name: str, user_name: str, message: str) -> str:
        help_dto = HelpDTO(
            command_prefix=self.command_prefix,
            user_name=user_name.lower(),
            channel_name=channel_name,
            bot_nick=self._bot_name.lower(),
            occurred_at=datetime.now(UTC),
            commands=self.commands,
            message=message,
        )

        return await self._handle_help_use_case.handle(help_dto)
