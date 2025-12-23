from datetime import datetime
from typing import Callable, Any, Awaitable

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from core.db import SessionLocal


class HelpCommandHandler:

    def __init__(
        self,
        command_prefix: str,
        chat_use_case_factory: Callable[[Session], ChatUseCase],
        commands_map: dict[str, str],
        nick_provider: Callable[[], str],
        post_message_fn: Callable[[str, Any], Awaitable[None]]
    ):
        self.command_prefix = command_prefix
        self._chat_use_case = chat_use_case_factory
        self.commands_map = commands_map
        self.nick_provider = nick_provider
        self.post_message_fn = post_message_fn

    async def handle(self, channel_name: str, ctx):
        bot_nick = self.nick_provider() or ""

        help_parts = ["📜 Доступные команды:"]
        for cmd, desc in self.commands_map.items():
            help_parts.append(f"{self.command_prefix}{cmd}: {desc}")
        help_text = " ".join(help_parts)

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), help_text, datetime.utcnow())

        await self.post_message_fn(help_text, ctx)
