from datetime import UTC, datetime

from app.platform.command.ask.application.handle_ask_use_case import HandleAskUseCase
from app.platform.command.ask.application.model import AskCommandDTO
from app.platform.command.domain.command_handler import CommandHandler


class AskCommandHandler(CommandHandler):
    def __init__(self, command_prefix: str, command_name: str, handle_ask_use_case: HandleAskUseCase):
        self.command_prefix = command_prefix
        self.command_name = command_name
        self._handle_ask_use_case = handle_ask_use_case
        self._bot_name: str | None = None

    def apply_bot_name(self, bot_name) -> None:
        self._bot_name = bot_name

    async def handle(self, channel_name: str, user_name: str, message: str) -> str:
        user_message = message[len(f"{self.command_prefix}{self.command_name}") :].strip()

        dto = AskCommandDTO(
            channel_name=channel_name,
            display_name=user_name,
            user_name=user_name.lower(),
            bot_nick=self._bot_name,
            occurred_at=datetime.now(UTC),
            message=user_message,
        )

        return await self._handle_ask_use_case.handle(dto)
