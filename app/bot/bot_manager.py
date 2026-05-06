import asyncio
from datetime import UTC, datetime

from app.bot.domain.model.status import BotStatus
from app.bot.presentation.api.model.response.action import BotActionResultResponse
from app.bot.presentation.api.model.response.status import BotStatusResponse
from app.core.logger.domain.logger import Logger
from app.core.network.api.client import ApiClient
from app.platform.auth.platform_auth import PlatformAuth
from app.platform.chat.infrastructure.twitch_platform_client import TwitchPlatformChatClient
from app.platform.domain.repository import PlatformRepository
from app.stream.application.usecase.handle_restore_stream_context_use_case import HandleRestoreStreamContextUseCase
from app.task.infrastructure.runner import BackgroundTaskRunner
from app.viewer.application.port.viewer_cache_port import ViewerCachePort


class BotManager:
    def __init__(
        self,
        logger: Logger,
        viewer_cache: ViewerCachePort,
        handle_restore_stream_use_case: HandleRestoreStreamContextUseCase,
        platform_chat_client: TwitchPlatformChatClient,
        task_runner: BackgroundTaskRunner,
        api_client: ApiClient,
    ):
        self._logger = logger.create_child(__name__)
        self._viewer_cache = viewer_cache
        self._handle_restore_stream_use_case = handle_restore_stream_use_case
        self._platform_chat_client = platform_chat_client
        self._task_runner = task_runner
        self._api_client = api_client

        self._status: BotStatus = BotStatus.STOPPED
        self._started_at: datetime | None = None
        self._last_error: str | None = None
        self._lock = asyncio.Lock()
        self._task: asyncio.Task | None = None

    def _on_bot_done(self, task: asyncio.Task) -> None:
        try:
            exc = task.exception()
            if exc:
                self._last_error = str(exc)
                self._logger.log_error(f"Twitch бот завершился с ошибкой: {exc}")
            else:
                self._logger.log_info("Twitch бот остановлен")
        except asyncio.CancelledError:
            self._logger.log_info("Задача Twitch бота отменена")

    def get_status(self) -> BotStatusResponse:
        started_at = self._started_at.isoformat() if self._started_at else None
        return BotStatusResponse(status=self._status, started_at=started_at, last_error=self._last_error)

    async def start_bot(
        self, channel_name: str, platform_auth: PlatformAuth, platform_repository: PlatformRepository
    ) -> BotActionResultResponse:
        async with self._lock:
            if self._task and not self._task.done():
                return BotActionResultResponse(**self.get_status().model_dump(), message="Бот уже запущен")

            bot_user = await platform_repository.get_authenticated_user()
            if not bot_user:
                raise ValueError("Не удалось получить профиль бота по токену (GET /users). Проверьте авторизацию.")
            bot_name = bot_user.display_name.lower()
            bot_user_id = bot_user.id

            self._platform_chat_client.init_client(platform_auth, channel_name, bot_name, bot_user_id)
            self._handle_restore_stream_use_case.handle(channel_name)

            await self._viewer_cache.warmup(channel_name)

            self._task_runner.start_all(
                channel_name=channel_name,
                bot_name=bot_name,
            )

            self._status = BotStatus.RUNNING
            self._started_at = datetime.now(UTC)
            self._last_error = None
            self._task = asyncio.create_task(self._platform_chat_client.start_chat())
            self._task.add_done_callback(self._on_bot_done)

            return BotActionResultResponse(**self.get_status().model_dump(), message="Запуск инициализирован")

    async def stop_bot(self) -> BotActionResultResponse:
        async with self._lock:
            task = self._task

            if not isinstance(task, asyncio.Task):
                self._logger.log_info("Попытка остановки, но бот не запущен")
                return BotActionResultResponse(**self.get_status().model_dump(), message="Бот уже остановлен")
            try:
                self._status: BotStatus = BotStatus.STOPPED
                await self._api_client.close()
                await self._task_runner.cancel_all()
                await self._platform_chat_client.stop_chat()
            except asyncio.CancelledError:
                self._logger.log_debug("Задача бота отменена")
            except Exception as e:
                self._logger.log_exception("Error stopping bot", e)

            return BotActionResultResponse(**self.get_status().model_dump(), message="Бот остановлен")
