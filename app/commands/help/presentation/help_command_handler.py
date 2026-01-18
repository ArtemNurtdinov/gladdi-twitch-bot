from collections.abc import Awaitable, Callable
from datetime import datetime

from app.commands.help.application.handle_help_use_case import HandleHelpUseCase
from app.commands.help.application.model import HelpDTO
from core.chat.interfaces import ChatContext


class HelpCommandHandler:
    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        handle_help_use_case: HandleHelpUseCase,
        commands: set[str],
        bot_nick: str,
        post_message_fn: Callable[[str, ChatContext], Awaitable[None]],
    ):
        self.command_prefix = command_prefix
        self.command_name = command_name
        self._handle_help_use_case = handle_help_use_case
        self.commands = commands
        self._bot_nick = bot_nick
        self.post_message_fn = post_message_fn

    async def handle(self, channel_name: str, display_name: str, chat_ctx: ChatContext):
        bot_nick = self._bot_nick.lower()

        dto = HelpDTO(
            command_prefix=self.command_prefix,
            command_name=self.command_name,
            user_name=display_name.lower(),
            channel_name=channel_name,
            bot_nick=bot_nick,
            occurred_at=datetime.utcnow(),
            commands=self.commands,
        )

        result = await self._handle_help_use_case.handle(dto)

        await self.post_message_fn(result, chat_ctx)
