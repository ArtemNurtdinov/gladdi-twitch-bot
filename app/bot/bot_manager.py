import asyncio
from datetime import UTC, datetime

from app.bot.domain.model.status import BotStatus
from app.bot.presentation.api.model.response.action import BotActionResultResponse
from app.bot.presentation.api.model.response.status import BotStatusResponse
from app.chat.application.job.chat_summarizer_job import ChatSummarizerJob
from app.core.logger.domain.logger import Logger
from app.core.network.api.client import ApiClient
from app.follow.infrastructure.jobs.followers_sync_job import FollowersSyncJob
from app.joke.application.job.post_joke_job import PostJokeJob
from app.minigame.application.job.minigame_tick_job import MinigameTickJob
from app.platform.auth.platform_auth import PlatformAuth
from app.platform.chat.infrastructure.twitch_platform_client import TwitchPlatformChatClient
from app.platform.domain.repository import PlatformRepository
from app.stream.application.job.stream_status_job import StreamStatusJob
from app.stream.application.usecase.handle_restore_stream_context_use_case import HandleRestoreStreamContextUseCase
from app.task.infrastructure.runner import BackgroundTaskRunner
from app.viewer.application.port.viewer_cache_port import ViewerCachePort
from app.viewer.session.application.job.viewer_time_job import ViewerTimeJob


class BotManager:
    def __init__(
        self,
        logger: Logger,
        viewer_cache: ViewerCachePort,
        handle_restore_stream_use_case: HandleRestoreStreamContextUseCase,
        platform_chat_client: TwitchPlatformChatClient,
        chat_summarizer_job: ChatSummarizerJob,
        post_joke_job: PostJokeJob,
        stream_status_job: StreamStatusJob,
        minigame_job: MinigameTickJob,
        viewer_time_job: ViewerTimeJob,
        followers_sync_job: FollowersSyncJob,
        task_runner: BackgroundTaskRunner,
        api_client: ApiClient,
    ):
        self._logger = logger.create_child(__name__)
        self._chat_summarizer_job = chat_summarizer_job
        self._minigame_job = minigame_job
        self._viewer_time_job = viewer_time_job
        self._followers_sync_job = followers_sync_job
        self._viewer_cache = viewer_cache
        self._handle_restore_stream_use_case = handle_restore_stream_use_case
        self._platform_chat_client = platform_chat_client
        self._post_joke_job = post_joke_job
        self._stream_status_job = stream_status_job
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

            try:
                await self._viewer_cache.warmup(channel_name)
            except Exception:
                self._logger.log_error("Не удалось прогреть cache")

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
