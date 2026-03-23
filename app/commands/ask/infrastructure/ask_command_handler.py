from datetime import datetime

from app.commands.ask.application.handle_ask_use_case import HandleAskUseCase
from app.commands.ask.application.model import AskCommandDTO
from app.platform.command.domain.command_handler import CommandHandler


class AskCommandHandlerImpl(CommandHandler):
    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        handle_ask_use_case: HandleAskUseCase,
        bot_nick: str,
    ):
        self.command_prefix = command_prefix
        self.command_name = command_name
        self._handle_ask_use_case = handle_ask_use_case
        self._bot_nick = bot_nick

    async def handle(self, channel_name: str, user_name: str, message: str) -> str:
        user_message = message[len(f"{self.command_prefix}{self.command_name}") :].strip()

        dto = AskCommandDTO(
            channel_name=channel_name,
            display_name=user_name,
            user_name=user_name.lower(),
            bot_nick=self._bot_nick,
            occurred_at=datetime.utcnow(),
            message=user_message,
        )

        return await self._handle_ask_use_case.handle(dto)
