from collections.abc import Awaitable, Callable
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
        post_message_fn: Callable[[str], Awaitable[None]],
        bot_nick: str,
    ):
        self.command_prefix = command_prefix
        self.command_name = command_name
        self._handle_ask_use_case = handle_ask_use_case
        self.post_message_fn = post_message_fn
        self._bot_nick = bot_nick

    async def handle_command(self, channel_name: str, user_name: str, user_message: str):
        user_message = user_message[len(f"{self.command_prefix}{self.command_name}") :].strip()

        dto = AskCommandDTO(
            channel_name=channel_name,
            display_name=user_name,
            user_name=user_name.lower(),
            bot_nick=self._bot_nick,
            occurred_at=datetime.utcnow(),
            message=user_message,
        )

        result = await self._handle_ask_use_case.handle(dto)
        await self.post_message_fn(result)
