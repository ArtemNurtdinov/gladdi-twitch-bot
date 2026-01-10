import asyncio
import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from app.ai.bootstrap import build_ai_providers
from app.battle.bootstrap import build_battle_providers
from app.betting.bootstrap import build_betting_providers
from app.chat.bootstrap import build_chat_providers
from app.commands.registry import CommandRegistry
from app.economy.bootstrap import build_economy_providers
from app.equipment.bootstrap import build_equipment_providers
from app.follow.bootstrap import build_follow_providers
from app.joke.bootstrap import build_joke_providers
from app.minigame.bootstrap import build_minigame_providers
from app.platform.auth import PlatformAuth
from app.platform.bot.bot import Bot
from app.platform.bot.bot_factory import BotFactory
from app.platform.bot.bot_settings import DEFAULT_SETTINGS, BotSettings
from app.platform.bot.schemas import BotActionResult, BotStatus, BotStatusEnum
from app.platform.providers import PlatformProviders
from app.stream.bootstrap import build_stream_providers
from app.user.bootstrap import build_user_providers
from app.viewer.bootstrap import build_viewer_providers
from bootstrap.config_provider import get_config
from core.bootstrap.background import build_background_providers
from core.bootstrap.telegram import build_telegram_providers
from core.chat.interfaces import CommandRouter

logger = logging.getLogger(__name__)


class BotManager:
    def __init__(
        self,
        platform_auth_factory: Callable[[str, str], PlatformAuth],
        platform_providers_builder: Callable[[PlatformAuth], PlatformProviders],
        chat_client_factory: Callable[[PlatformAuth, BotSettings], Any],
        command_router_builder: Callable[[BotSettings, CommandRegistry, Bot], CommandRouter],
        settings: BotSettings = DEFAULT_SETTINGS,
    ):
        self._platform_auth_factory = platform_auth_factory
        self._platform_providers_builder = platform_providers_builder
        self._chat_client_factory = chat_client_factory
        self._command_router_builder = command_router_builder
        self._settings = settings

        self._bot: Bot | None = None
        self._chat_client: Any = None
        self._task: asyncio.Task | None = None
        self._status: BotStatusEnum = BotStatusEnum.STOPPED
        self._started_at: datetime | None = None
        self._last_error: str | None = None
        self._lock = asyncio.Lock()
        self._platform_providers: PlatformProviders | None = None

    def _ensure_credentials(self, auth: PlatformAuth) -> None:
        missing = []
        if not auth.client_id:
            missing.append("client_id")
        if not auth.client_secret:
            missing.append("client_secret")
        if not auth.refresh_token:
            missing.append("refresh_token")
        if not auth.access_token:
            missing.append("access_token")

        if missing:
            raise ValueError(f"Недостаточно данных для авторизации платформы: {', '.join(missing)}")

    def _reset_state(self):
        self._bot = None
        self._chat_client = None
        self._task = None
        self._status = BotStatusEnum.STOPPED
        self._started_at = None
        self._platform_providers = None

    def _on_bot_done(self, task: asyncio.Task) -> None:
        try:
            exc = task.exception()
            if exc:
                self._last_error = str(exc)
                logger.error(f"Twitch бот завершился с ошибкой: {exc}")
            else:
                logger.info("Twitch бот остановлен")
        except asyncio.CancelledError:
            logger.info("Задача Twitch бота отменена")
        finally:
            self._reset_state()

    def get_status(self) -> BotStatus:
        started_at = self._started_at.isoformat() if self._started_at else None
        return BotStatus(status=self._status, started_at=started_at, last_error=self._last_error)

    async def start_bot(self, access_token: str, refresh_token: str) -> BotActionResult:
        async with self._lock:
            if self._task and not self._task.done():
                return BotActionResult(**self.get_status().model_dump(), message="Бот уже запущен")

            auth = self._platform_auth_factory(access_token, refresh_token)
            self._ensure_credentials(auth)

            platform_providers = self._platform_providers_builder(auth)
            self._platform_providers = platform_providers
            streaming_platform = platform_providers.streaming_platform

            stream_providers = build_stream_providers(streaming_platform)
            ai_providers = build_ai_providers(config=get_config())
            chat_providers = build_chat_providers()
            follow_providers = build_follow_providers(streaming_platform)
            joke_providers = build_joke_providers()
            user_providers = build_user_providers(streaming_platform)
            viewer_providers = build_viewer_providers()
            economy_providers = build_economy_providers()
            equipment_providers = build_equipment_providers()
            minigame_providers = build_minigame_providers()
            battle_providers = build_battle_providers()
            betting_providers = build_betting_providers()
            background_providers = build_background_providers()
            telegram_providers = build_telegram_providers()
            self._chat_client = self._chat_client_factory(platform_providers.platform_auth, self._settings)
            self._bot = BotFactory(
                platform_providers,
                ai_providers,
                chat_providers,
                follow_providers,
                joke_providers,
                user_providers,
                viewer_providers,
                stream_providers,
                economy_providers,
                minigame_providers,
                equipment_providers,
                battle_providers,
                betting_providers,
                background_providers,
                telegram_providers,
                self._settings,
                self._command_router_builder,
            ).create(chat_outbound=self._chat_client)
            await self._bot.warmup()
            await self._bot.start_background_tasks()
            self._status = BotStatusEnum.RUNNING
            self._started_at = datetime.utcnow()
            self._last_error = None

            self._task = asyncio.create_task(self._chat_client.start())
            self._task.add_done_callback(self._on_bot_done)

            return BotActionResult(**self.get_status().model_dump(), message="Запуск инициализирован")

    async def stop_bot(self) -> BotActionResult:
        async with self._lock:
            task = self._task
            bot = self._bot
            platform_api_service = self._platform_providers.api_client if self._platform_providers else None

            if not isinstance(task, asyncio.Task):
                logger.info("Попытка остановки, но бот не запущен")
                return BotActionResult(**self.get_status().model_dump(), message="Бот уже остановлен")
            try:
                if self._chat_client:
                    await self._chat_client.stop()
                if platform_api_service:
                    await platform_api_service.aclose()
                if bot:
                    await bot.close()
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        logger.debug("Задача бота отменена")
            finally:
                self._reset_state()

            return BotActionResult(**self.get_status().model_dump(), message="Бот остановлен")
