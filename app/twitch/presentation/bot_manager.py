import asyncio
import logging
from datetime import datetime
from typing import Optional

from app.twitch.bootstrap.twitch_bot_settings import DEFAULT_SETTINGS
from app.twitch.infrastructure.twitch_api_service import TwitchApiService
from app.twitch.infrastructure.auth import TwitchAuth
from app.twitch.bootstrap.twitch import build_twitch_providers
from app.stream.bootstrap import build_stream_providers
from app.economy.bootstrap import build_economy_providers
from app.equipment.bootstrap import build_equipment_providers
from app.minigame.bootstrap import build_minigame_providers
from app.ai.bootstrap import build_ai_providers
from app.battle.bootstrap import build_battle_providers
from app.betting.bootstrap import build_betting_providers
from app.chat.bootstrap import build_chat_providers
from app.follow.bootstrap import build_follow_providers
from app.joke.bootstrap import build_joke_providers
from app.user.bootstrap import build_user_providers
from app.viewer.bootstrap import build_viewer_providers
from core.bootstrap.background import build_background_providers
from core.bootstrap.telegram import build_telegram_providers
from app.twitch.presentation.twitch_schemas import BotActionResult, BotStatus, BotStatusEnum
from app.twitch.bootstrap.bot_factory import BotFactory
from app.twitch.presentation.twitch_bot import Bot as TwitchBot

logger = logging.getLogger(__name__)


class BotManager:

    def __init__(self):
        self._bot: Optional[TwitchBot] = None
        self._task: Optional[asyncio.Task] = None
        self._status: BotStatusEnum = BotStatusEnum.STOPPED
        self._started_at: Optional[datetime] = None
        self._last_error: Optional[str] = None
        self._lock = asyncio.Lock()
        self._twitch_api_service: Optional[TwitchApiService] = None

    def _ensure_credentials(self, auth: TwitchAuth) -> None:
        missing = []
        if not auth.client_id:
            missing.append("TWITCH_CLIENT_ID")
        if not auth.client_secret:
            missing.append("TWITCH_CLIENT_SECRET")
        if not auth.refresh_token:
            missing.append("refresh_token")
        if not auth.access_token:
            missing.append("access_token")

        if missing:
            raise ValueError(f"Недостаточно данных для авторизации Twitch: {', '.join(missing)}")

    def _reset_state(self):
        self._bot = None
        self._task = None
        self._status = BotStatusEnum.STOPPED
        self._started_at = None
        self._twitch_api_service = None

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

            auth = TwitchAuth(access_token=access_token, refresh_token=refresh_token, logger=logger)
            self._ensure_credentials(auth)

            twitch_providers = build_twitch_providers(auth)
            self._twitch_api_service = twitch_providers.twitch_api_service
            stream_providers = build_stream_providers(twitch_providers.twitch_api_service)
            ai_providers = build_ai_providers()
            chat_providers = build_chat_providers()
            follow_providers = build_follow_providers(twitch_providers.twitch_api_service)
            joke_providers = build_joke_providers()
            user_providers = build_user_providers(twitch_providers.twitch_api_service)
            viewer_providers = build_viewer_providers()
            economy_providers = build_economy_providers()
            equipment_providers = build_equipment_providers()
            minigame_providers = build_minigame_providers()
            battle_providers = build_battle_providers()
            betting_providers = build_betting_providers()
            background_providers = build_background_providers()
            telegram_providers = build_telegram_providers()
            self._bot = BotFactory(
                twitch_providers,
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
                DEFAULT_SETTINGS
            ).create()
            self._status = BotStatusEnum.RUNNING
            self._started_at = datetime.utcnow()
            self._last_error = None

            self._task = asyncio.create_task(self._bot.start())
            self._task.add_done_callback(self._on_bot_done)

            return BotActionResult(**self.get_status().model_dump(), message="Запуск инициализирован")

    async def stop_bot(self) -> BotActionResult:
        async with self._lock:
            task = self._task
            bot = self._bot
            twitch_api_service = self._twitch_api_service

            if not isinstance(task, asyncio.Task):
                logger.info("Попытка остановки, но бот не запущен")
                return BotActionResult(**self.get_status().model_dump(), message="Бот уже остановлен")
            try:
                if bot:
                    await bot.close()
                if twitch_api_service:
                    await twitch_api_service.aclose()
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        logger.debug("Задача бота отменена")
            finally:
                self._reset_state()

            return BotActionResult(**self.get_status().model_dump(), message="Бот остановлен")
