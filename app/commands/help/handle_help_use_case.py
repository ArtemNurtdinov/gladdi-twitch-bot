from collections.abc import Callable
from contextlib import AbstractContextManager

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from app.commands.help.model import HelpDTO
from core.provider import Provider


class HandleHelpUseCase:
    def __init__(self, chat_use_case_provider: Provider[ChatUseCase]):
        self._chat_use_case_provider = chat_use_case_provider

    async def handle(
        self,
        db_session_provider: Callable[[], AbstractContextManager[Session]],
        command_help: HelpDTO,
    ) -> str:
        help_parts = ["📜 Доступные команды:"]
        for cmd in command_help.commands:
            help_parts.append(f"{command_help.command_prefix}{cmd}")
        help_text = " ".join(help_parts)

        with db_session_provider() as db:
            self._chat_use_case_provider.get(db).save_chat_message(
                channel_name=command_help.channel_name,
                user_name=command_help.bot_nick,
                content=help_text,
                current_time=command_help.occurred_at,
            )

        return help_text
