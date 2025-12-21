import asyncio
import logging
from datetime import datetime
from typing import Optional

from app.ai.domain.ai_service import AIService
from app.ai.data.ai_repository import AIRepositoryImpl
from app.twitch.infrastructure.twitch_api_service import TwitchApiService
from app.twitch.presentation.auth import TwitchAuth
from app.twitch.presentation.twitch_schemas import BotActionResult, BotStatus, BotStatusEnum
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

            auth = TwitchAuth(access_token=access_token, refresh_token=refresh_token)
            self._ensure_credentials(auth)

            ai_service = AIService(AIRepositoryImpl())
            twitch_api_service = TwitchApiService(auth)

            self._bot = TwitchBot(auth, twitch_api_service, ai_service)
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

            if not isinstance(task, asyncio.Task):
                logger.info("Попытка остановки, но бот не запущен")
                return BotActionResult(**self.get_status().model_dump(), message="Бот уже остановлен")
            try:
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
