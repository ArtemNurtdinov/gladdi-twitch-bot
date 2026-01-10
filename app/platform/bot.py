from __future__ import annotations

import asyncio
import logging

from app.chat.application.model import ChatSummaryState
from app.commands.chat.chat_event_handler import ChatEventHandler
from app.platform.providers import PlatformProviders
from app.twitch.bootstrap.bot_settings import BotSettings
from app.user.bootstrap import UserProviders
from core.background.bot_tasks import BotBackgroundTasks
from core.chat.interfaces import CommandRouter
from core.chat.outbound import ChatOutbound

logger = logging.getLogger(__name__)


class Bot:
    def __init__(self, platform_providers: PlatformProviders, user_providers: UserProviders, settings: BotSettings):
        self._settings = settings
        self._platform = platform_providers
        self._user = user_providers
        self._chat_client: ChatOutbound | None = None
        self.nick = settings.channel_name or "bot"

        self._chat_summary_state = ChatSummaryState()
        self._battle_waiting_user_ref = {"value": None}

        self.minigame_orchestrator = None
        self._background_tasks: BotBackgroundTasks | None = None
        self._command_registry = None
        self._chat_event_handler: ChatEventHandler | None = None
        self._command_router: CommandRouter | None = None

    @property
    def battle_waiting_user_ref(self):
        return self._battle_waiting_user_ref

    @property
    def chat_summary_state(self):
        return self._chat_summary_state

    def set_minigame_orchestrator(self, orchestrator):
        self.minigame_orchestrator = orchestrator

    def set_background_tasks(self, background_tasks: BotBackgroundTasks):
        self._background_tasks = background_tasks

    def set_command_registry(self, command_registry):
        self._command_registry = command_registry

    def set_chat_event_handler(self, chat_event_handler: ChatEventHandler):
        self._chat_event_handler = chat_event_handler

    @property
    def chat_event_handler(self) -> ChatEventHandler | None:
        return self._chat_event_handler

    def set_command_router(self, command_router: CommandRouter):
        self._command_router = command_router

    def set_chat_client(self, chat_client: ChatOutbound):
        self._chat_client = chat_client

    @property
    def command_router(self) -> CommandRouter | None:
        return self._command_router

    async def warmup(self):
        await self._warmup_broadcaster_id()

    async def start_background_tasks(self):
        await self._start_background_tasks()

    async def _warmup_broadcaster_id(self):
        try:
            if not self._settings.channel_name:
                return
            channel_name = self._settings.channel_name
            await self._user.user_cache.warmup(channel_name)
        except Exception as e:
            logger.error(f"Не удалось прогреть кеш ID канала: {e}")

    async def _start_background_tasks(self):
        if not self._background_tasks:
            return
        self._background_tasks.start_all()

    async def close(self):
        if self._background_tasks:
            await self._background_tasks.stop_all()

    def _split_text(self, text, max_length=500):
        if len(text) <= max_length:
            return [text]

        messages = []
        while text:
            if len(text) <= max_length:
                messages.append(text)
                break

            split_pos = text.rfind(" ", 0, max_length)
            if split_pos == -1:
                split_pos = max_length

            part = text[:split_pos].strip()
            if part:
                messages.append(part)

            text = text[split_pos:].strip()
        return messages

    async def post_message_in_twitch_chat(self, message: str, ctx):
        if self._chat_client:
            await self._chat_client.post_message(message, ctx)
            return
        messages = self._split_text(message)
        for msg in messages:
            await ctx.send_channel(msg)
            await asyncio.sleep(0.3)

    async def send_channel_message(self, channel_name: str, message: str):
        if self._chat_client:
            await self._chat_client.send_channel_message(channel_name, message)
            return
        logger.warning("Нет chat_client для отправки сообщения в канал %s", channel_name)
