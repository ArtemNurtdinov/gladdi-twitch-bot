import asyncio
from datetime import UTC, datetime

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.ai.gen.llm.application.usecase.generate_response_use_case import GenerateResponseUseCase
from app.ai.gen.llm.domain.llm_repository import LLMRepository
from app.ai.gen.prompt.domain.system_prompt_repository import SystemPromptRepository
from app.battle.application.usecase.battle_use_case import BattleUseCase
from app.bot.domain.model.status import BotStatus
from app.bot.presentation.api.model.response.action import BotActionResultResponse
from app.bot.presentation.api.model.response.status import BotStatusResponse
from app.chat.application.job.chat_summarizer_job import ChatSummarizerJob
from app.chat.application.model.chat_summary_state import ChatSummaryState
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
from app.joke.application.job.post_joke_job import PostJokeJob
from app.joke.di.container import JokeContainer
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
from app.stream.application.usecase.handle_restore_stream_context_use_case import HandleRestoreStreamContextUseCase
from app.stream.domain.repo import StreamRepository
from app.task.domain.model.task import Task
from app.task.domain.runner import TaskRunner
from app.task.infrastructure.runner import BackgroundTaskRunner
from app.viewer.application.port.viewer_cache_port import ViewerCachePort
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
        self._viewer_cache = viewer_cache
        self._handle_restore_stream_use_case = handle_restore_stream_use_case
        self._platform_chat_client = platform_chat_client
        self._post_joke_job = post_joke_job

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
        generate_response_use_case_factory: SessionScopedFactory[GenerateResponseUseCase],
        conversation_service_factory: SessionScopedFactory[ConversationService],
        system_prompt_repository_factory: SessionScopedFactory[SystemPromptRepository],
        llm_repository_factory: SessionScopedFactory[LLMRepository],
        joke_container: JokeContainer,
        platform_auth: PlatformAuth,
        token_checker_job: TokenCheckerJob,
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
            chat_summary_state = ChatSummaryState()

            self._platform_chat_client.init_client(platform_auth, channel_name, bot_name, bot_user_id, battle_waiting_user)
            self._handle_restore_stream_use_case.handle(channel_name)

            try:
                await self._viewer_cache.warmup(channel_name)
            except Exception:
                self._logger.log_error("Не удалось прогреть cache")

            self._post_joke_job.apply_channel(channel_name, bot_name)

            stream_status_job = self._platform_container.stream_status_job(
                channel_name=channel_name,
                user_cache=self._viewer_cache,
                platform_repository=platform_repository,
                minigame_repository=self._minigame_repository,
                notification_repository=self._notification_repository,
                notification_group_id=self._telegram_config.group_id,
                generate_response_use_case_factory=generate_response_use_case_factory,
                state=chat_summary_state,
                stream_repository_factory=self._stream_repository_factory,
                viewer_repository_factory=self._viewer_repository_factory,
                battle_use_case=self._battle_use_case,
                economy_policy_factory=self._economy_policy_factory,
                chat_use_case=self._chat_use_case,
                conversation_service_factory=conversation_service_factory,
            )

            self._chat_summarizer_job.apply_channel(channel_name)
            self._chat_summarizer_job.apply_summary_state(chat_summary_state)

            minigame_job: MinigameTickJob = MinigameTickJob(
                channel_name=channel_name,
                handle_minigame_tick_use_case=self._platform_container.handle_minigame_tick_use_case(
                    minigame_repository=self._minigame_repository,
                    economy_policy_factory=self._economy_policy_factory,
                    chat_use_case=self._chat_use_case,
                    stream_repository_factory=self._stream_repository_factory,
                    get_used_words_use_case=self._get_used_word_use_case,
                    add_used_words_use_case=self._add_used_word_use_case,
                    conversation_service_factory=conversation_service_factory,
                    get_user_equipment_use_case=self._get_user_equipment_use_case,
                    system_prompt_repository_factory=system_prompt_repository_factory,
                    llm_repository_factory=llm_repository_factory,
                    prefix=self._config.prefix,
                    number_guess_name=self._config.command_guess,
                    command_guess_word=self._config.command_guess_word,
                    command_guess_letter=self._config.command_guess_letter,
                    rps_command_name=self._config.command_rps,
                    send_channel_message=self._platform_chat_client.send_channel_message,
                    bot_name=bot_name,
                ),
                logger=self._logger,
            )

            viewer_time_job = self._platform_container.viewer_time_job(
                stream_repository_factory=self._stream_repository_factory,
                viewer_repository_factory=self._viewer_repository_factory,
                economy_policy_factory=self._economy_policy_factory,
                viewer_cache=self._viewer_cache,
                platform_repository=platform_repository,
                channel_name=channel_name,
                bot_name=bot_name,
            )

            followers_sync_job = self._platform_container.followers_sync_job(
                channel_name=channel_name,
                platform_repository=platform_repository,
                followers_repository_factory=self._followers_repository_factory,
            )

            jobs = [
                self._post_joke_job,
                token_checker_job,
                stream_status_job,
                self._chat_summarizer_job,
                minigame_job,
                viewer_time_job,
                followers_sync_job,
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
