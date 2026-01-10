from __future__ import annotations

import logging

from app.chat.application.model import ChatSummaryState
from app.platform.bot.bot_settings import BotSettings
from app.platform.providers import PlatformProviders
from app.user.bootstrap import UserProviders
from core.background.bot_tasks import BotBackgroundTasks

logger = logging.getLogger(__name__)


class Bot:
    def __init__(self, platform_providers: PlatformProviders, user_providers: UserProviders, settings: BotSettings):
        self._settings = settings
        self._platform = platform_providers
        self._user = user_providers
        self.nick = settings.bot_name

        self._chat_summary_state = ChatSummaryState()
        self._battle_waiting_user_ref = {"value": None}

        self.minigame_orchestrator = None
        self._background_tasks: BotBackgroundTasks | None = None

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
