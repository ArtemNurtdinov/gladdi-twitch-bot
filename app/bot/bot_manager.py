import asyncio
from datetime import UTC, datetime

from app.battle.application.usecase.battle_use_case import BattleUseCase
from app.bot.domain.model.status import BotStatus
from app.bot.presentation.api.model.response.action import BotActionResultResponse
from app.bot.presentation.api.model.response.status import BotStatusResponse
from app.chat.application.job.chat_summarizer_job import ChatSummarizerJob
from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.core.common.session.session_scoped_factory import SessionScopedFactory
from app.core.config.domain.model.bot import BotConfig
from app.core.config.domain.model.intent_detector import IntentDetectorConfig
from app.core.config.domain.model.llmbox import LLMBoxConfig
from app.core.config.domain.model.telegram import TelegramConfig
from app.core.logger.domain.logger import Logger
from app.core.network.api.client import ApiClient
from app.economy.domain.economy_policy import EconomyPolicy
from app.equipment.application.get_user_equipment_use_case import GetUserEquipmentUseCase
from app.follow.domain.repo import FollowersRepository
from app.follow.infrastructure.jobs.followers_sync_job import FollowersSyncJob
from app.joke.application.job.post_joke_job import PostJokeJob
from app.minigame.application.job.minigame_tick_job import MinigameTickJob
from app.minigame.application.use_case.add_used_word_use_case import AddUsedWordsUseCase
from app.minigame.application.use_case.get_used_words_use_case import GetUsedWordsUseCase
from app.minigame.domain.minigame_repository import MinigameRepository
from app.notification.domain.repository import NotificationRepository
from app.platform.auth.application.job.token_checker_job import TokenCheckerJob
from app.platform.auth.platform_auth import PlatformAuth
from app.platform.chat.infrastructure.twitch_platform_client import TwitchPlatformChatClient
from app.platform.di.container import PlatformContainer
from app.platform.domain.repository import PlatformRepository
from app.stream.application.job.stream_status_job import StreamStatusJob
from app.stream.application.usecase.handle_restore_stream_context_use_case import HandleRestoreStreamContextUseCase
from app.stream.domain.repo import StreamRepository
from app.task.domain.model.task import Task
from app.task.domain.runner import TaskRunner
from app.task.infrastructure.runner import BackgroundTaskRunner
from app.viewer.application.port.viewer_cache_port import ViewerCachePort
from app.viewer.session.application.job.viewer_time_job import ViewerTimeJob
from app.viewer.session.domain.repository import ViewerRepository


class BotManager:
    def __init__(
        self,
        config: BotConfig,
        telegram_config: TelegramConfig,
        llmbox_config: LLMBoxConfig,
        intent_detector_config: IntentDetectorConfig,
        logger: Logger,
        minigame_repository: MinigameRepository,
        get_used_word_use_case: GetUsedWordsUseCase,
        add_used_word_use_case: AddUsedWordsUseCase,
        stream_repository_factory: SessionScopedFactory[StreamRepository],
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        chat_use_case: ChatUseCase,
        followers_repository_factory: SessionScopedFactory[FollowersRepository],
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        notification_repository: NotificationRepository,
        battle_use_case: BattleUseCase,
        platform_container: PlatformContainer,
        viewer_repository_factory: SessionScopedFactory[ViewerRepository],
        chat_summarizer_job: ChatSummarizerJob,
        viewer_cache: ViewerCachePort,
        handle_restore_stream_use_case: HandleRestoreStreamContextUseCase,
        platform_chat_client: TwitchPlatformChatClient,
        post_joke_job: PostJokeJob,
        stream_status_job: StreamStatusJob,
        token_checker_job: TokenCheckerJob,
        minigame_job: MinigameTickJob,
        viewer_time_job: ViewerTimeJob,
        followers_sync_job: FollowersSyncJob,
    ):
        self._config = config
        self._telegram_config = telegram_config
        self._llmbox_config = llmbox_config
        self._intent_detector_config = intent_detector_config
        self._logger = logger.create_child(__name__)

        self._minigame_repository = minigame_repository
        self._get_used_word_use_case = get_used_word_use_case
        self._add_used_word_use_case = add_used_word_use_case
        self._stream_repository_factory = stream_repository_factory
        self._economy_policy_factory = economy_policy_factory
        self._chat_use_case = chat_use_case
        self._followers_repository_factory = followers_repository_factory
        self._get_user_equipment_use_case = get_user_equipment_use_case
        self._notification_repository = notification_repository
        self._battle_use_case = battle_use_case
        self._platform_container = platform_container
        self._viewer_repository_factory = viewer_repository_factory
        self._chat_summarizer_job = chat_summarizer_job
        self._minigame_job = minigame_job
        self._viewer_time_job = viewer_time_job
        self._followers_sync_job = followers_sync_job
        self._viewer_cache = viewer_cache
        self._handle_restore_stream_use_case = handle_restore_stream_use_case
        self._platform_chat_client = platform_chat_client
        self._post_joke_job = post_joke_job
        self._stream_status_job = stream_status_job
        self._token_checker_job = token_checker_job

        self._status: BotStatus = BotStatus.STOPPED
        self._started_at: datetime | None = None
        self._last_error: str | None = None
        self._lock = asyncio.Lock()

        self._api_client: ApiClient | None = None
        self._task_runner: TaskRunner | None = None

        self._task: asyncio.Task | None = None

    def _reset_state(self):
        self._task_runner = None
        self._platform_chat_client = None
        self._task = None
        self._started_at = None

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
        finally:
            self._reset_state()

    def get_status(self) -> BotStatusResponse:
        started_at = self._started_at.isoformat() if self._started_at else None
        return BotStatusResponse(status=self._status, started_at=started_at, last_error=self._last_error)

    async def start_bot(
        self,
        channel_name: str,
        platform_auth: PlatformAuth,
        platform_repository: PlatformRepository,
        api_client: ApiClient,
    ) -> BotActionResultResponse:
        async with self._lock:
            if self._task and not self._task.done():
                return BotActionResultResponse(**self.get_status().model_dump(), message="Бот уже запущен")

            self._api_client = api_client

            bot_user = await platform_repository.get_authenticated_user()
            if not bot_user:
                raise ValueError("Не удалось получить профиль бота по токену (GET /users). Проверьте авторизацию.")
            bot_name = bot_user.display_name.lower()
            bot_user_id = bot_user.id
            battle_waiting_user = {"value": None}

            self._platform_chat_client.init_client(platform_auth, channel_name, bot_name, bot_user_id, battle_waiting_user)
            self._handle_restore_stream_use_case.handle(channel_name)

            try:
                await self._viewer_cache.warmup(channel_name)
            except Exception:
                self._logger.log_error("Не удалось прогреть cache")

            self._post_joke_job.apply_channel(channel_name, bot_name)
            self._stream_status_job.apply_channel(channel_name, bot_name)
            self._chat_summarizer_job.apply_channel(channel_name, bot_name)
            self._minigame_job.apply_channel(channel_name, bot_name)
            self._viewer_time_job.apply_channel(channel_name, bot_name)
            self._followers_sync_job.apply_channel(channel_name, bot_name)

            jobs = [
                self._post_joke_job,
                self._token_checker_job,
                self._stream_status_job,
                self._chat_summarizer_job,
                self._minigame_job,
                self._viewer_time_job,
                self._followers_sync_job,
            ]

            tasks = [Task(job.name, job.run) for job in jobs]
            self._task_runner: TaskRunner = BackgroundTaskRunner(tasks)
            self._task_runner.start_all()

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
