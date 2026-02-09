import asyncio
import logging
from collections.abc import Callable
from datetime import datetime

from app.commands.presentation.commands_registry import CommandRegistry
from app.platform.auth import PlatformAuth
from app.platform.bot.bot import Bot
from app.platform.bot.bot_settings import DEFAULT_SETTINGS, BotSettings
from app.platform.bot.schemas import BotActionResult, BotStatus, BotStatusEnum
from app.platform.providers import PlatformProviders
from bootstrap.bot_composition import build_bot_composition
from core.chat.interfaces import CommandRouter
from core.chat.outbound import ChatOutbound

logger = logging.getLogger(__name__)


class BotManager:
    def __init__(
        self,
        platform_auth_factory: Callable[[str, str, str, str], PlatformAuth],
        platform_providers_builder: Callable[[PlatformAuth], PlatformProviders],
        chat_client_factory: Callable[[PlatformAuth, BotSettings, str | None], ChatOutbound],
        command_router_builder: Callable[[BotSettings, CommandRegistry, Bot], CommandRouter],
        settings: BotSettings = DEFAULT_SETTINGS,
    ):
        self._platform_auth_factory = platform_auth_factory
        self._platform_providers_builder = platform_providers_builder
        self._chat_client_factory = chat_client_factory
        self._command_router_builder = command_router_builder
        self._settings = settings

        self._bot: Bot | None = None
        self._chat_client: ChatOutbound | None = None
        self._task: asyncio.Task | None = None
        self._status: BotStatusEnum = BotStatusEnum.STOPPED
        self._started_at: datetime | None = None
        self._last_error: str | None = None
        self._lock = asyncio.Lock()
        self._platform_providers: PlatformProviders | None = None

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

    async def start_bot(
        self,
        access_token: str,
        refresh_token: str,
        tg_bot_token: str,
        llmbox_host: str,
        intent_detector_host: str,
        client_id: str,
        client_secret: str,
    ) -> BotActionResult:
        async with self._lock:
            if self._task and not self._task.done():
                return BotActionResult(**self.get_status().model_dump(), message="Бот уже запущен")

            composition = await build_bot_composition(
                access_token=access_token,
                refresh_token=refresh_token,
                tg_bot_token=tg_bot_token,
                llmbox_host=llmbox_host,
                intent_detector_host=intent_detector_host,
                client_id=client_id,
                client_secret=client_secret,
                settings=self._settings,
                platform_auth_factory=self._platform_auth_factory,
                platform_providers_builder=self._platform_providers_builder,
                chat_client_factory=self._chat_client_factory,
                command_router_builder=self._command_router_builder,
            )
            self._platform_providers = composition.platform_providers
            self._chat_client = composition.chat_client
            self._bot = composition.bot
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
