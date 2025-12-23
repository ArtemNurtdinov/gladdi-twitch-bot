import asyncio
from datetime import datetime
from typing import Callable

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from core.db import SessionLocal


class HelpCommandHandler:

    def __init__(
        self,
        chat_use_case_factory: Callable[[Session], ChatUseCase],
        prefix: str,
        commands_map: dict[str, str],
        nick_provider: Callable[[], str],
        split_text_fn: Callable[[str], list[str]],
    ):
        self._chat_use_case = chat_use_case_factory
        self.prefix = prefix
        self.commands_map = commands_map
        self.nick_provider = nick_provider
        self.split_text = split_text_fn

    async def handle(self, ctx):
        channel_name = ctx.channel.name
        bot_nick = self.nick_provider() or ""

        help_parts = ["📜 Доступные команды:"]
        for cmd, desc in self.commands_map.items():
            help_parts.append(f"{self.prefix}{cmd}: {desc}")
        help_text = " ".join(help_parts)

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), help_text, datetime.utcnow())

        messages = self.split_text(help_text)
        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)
