from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.twitch.application.interaction.help.dto import HelpDTO
from app.chat.application.chat_use_case_provider import ChatUseCaseProvider


class HandleHelpUseCase:

    def __init__(self, chat_use_case_provider: ChatUseCaseProvider):
        self._chat_use_case_provider = chat_use_case_provider

    async def handle(
        self,
        db_session_provider: Callable[[], ContextManager[Session]],
        command_help_dto: HelpDTO,
    ) -> str:
        help_parts = ["📜 Доступные команды:"]
        for cmd in command_help_dto.commands:
            help_parts.append(f"{command_help_dto.command_prefix}{cmd}")
        help_text = " ".join(help_parts)

        with db_session_provider() as db:
            self._chat_use_case_provider.get(db).save_chat_message(
                channel_name=command_help_dto.channel_name,
                user_name=command_help_dto.bot_nick,
                content=help_text,
                current_time=command_help_dto.occurred_at,
            )

        return help_text
