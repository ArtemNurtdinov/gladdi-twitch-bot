from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.ai.gen.llm.application.usecase.generate_response_use_case import GenerateResponseUseCase
from app.ai.gen.llm.domain.llm_repository import LLMRepository
from app.ai.gen.prompt.domain.system_prompt_repository import SystemPromptRepository
from app.battle.application.usecase.battle_use_case import BattleUseCase
from app.bot.bot_manager import BotManager
from app.chat.application.job.chat_summarizer_job import ChatSummarizerJob
from app.chat.application.model.chat_summary_state import ChatSummaryState
from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.chat.application.usecase.handle_chat_summarizer_use_case import HandleChatSummarizerUseCase
from app.chat.domain.repo import ChatRepository
from app.chat.infrastructure.uow.chat_summarizer_uow import SqlAlchemyChatSummarizerUnitOfWorkFactory
from app.chat.infrastructure.uow.chat_use_case_uow import SqlAlchemyChatUseCaseUnitOfWorkFactory
from app.core.common.session.session_scoped_factory import SessionScopedFactory
from app.core.logger.domain.logger import Logger
from app.core.network.api.client import ApiClient
from app.economy.domain.economy_policy import EconomyPolicy
from app.equipment.application.get_user_equipment_use_case import GetUserEquipmentUseCase
from app.follow.application.usecases.handle_followers_sync_use_case import HandleFollowersSyncUseCase
from app.follow.domain.repo import FollowersRepository
from app.follow.infrastructure.jobs.followers_sync_job import FollowersSyncJob
from app.follow.infrastructure.uow.followers_sync_uow import SqlAlchemyFollowersSyncUnitOfWorkFactory
from app.joke.application.job.post_joke_job import PostJokeJob
from app.joke.application.usecase.handle_post_joke_use_case import HandlePostJokeUseCase
from app.joke.domain.repository import JokesConfigurationRepository
from app.joke.infrastructure.uow.joke_uow import SqlAlchemyJokeUnitOfWorkFactory
from app.minigame.application.job.minigame_tick_job import MinigameTickJob
from app.minigame.application.use_case.add_used_word_use_case import AddUsedWordsUseCase
from app.minigame.application.use_case.finish_expired_games_use_case import FinishExpiredGamesUseCase
from app.minigame.application.use_case.finish_rps_use_case import FinishRpsUseCase
from app.minigame.application.use_case.get_used_words_use_case import GetUsedWordsUseCase
from app.minigame.application.use_case.handle_minigame_tick_use_case import HandleMinigameTickUseCase
from app.minigame.application.use_case.start_number_guess_game_use_case import StartNumberGuessGameUseCase
from app.minigame.application.use_case.start_rps_game_use_case import StartRpsGameUseCase
from app.minigame.application.use_case.start_word_game_use_case import StartWordGameUseCase
from app.minigame.domain.minigame_repository import MinigameRepository
from app.minigame.infrastructure.uow.minigame_uow import SqlAlchemyMinigameUnitOfWorkFactory
from app.notification.domain.repository import NotificationRepository
from app.platform.auth.application.job.token_checker_job import TokenCheckerJob
from app.platform.auth.application.usecase.handle_token_checker_use_case import HandleTokenCheckerUseCase
from app.platform.auth.platform_auth import PlatformAuth
from app.platform.chat.infrastructure.twitch_platform_client import TwitchPlatformChatClient
from app.platform.domain.repository import PlatformRepository
from app.stream.application.job.stream_status_job import StreamStatusJob
from app.stream.application.usecase.handle_restore_stream_context_use_case import HandleRestoreStreamContextUseCase
from app.stream.application.usecase.handle_stream_status_use_case import HandleStreamStatusUseCase
from app.stream.domain.repo import StreamRepository
from app.stream.infrastructure.uow.restore_stream_context_uow import SqlAlchemyRestoreStreamContextUnitOfWorkFactory
from app.stream.infrastructure.uow.stream_status_uow import SqlAlchemyStreamStatusUnitOfWorkFactory
from app.task.domain.model.task import Task
from app.task.infrastructure.runner import BackgroundTaskRunner
from app.viewer.infrastructure.cache.viewer_cache_service import ViewerCacheService
from app.viewer.session.application.job.viewer_time_job import ViewerTimeJob
from app.viewer.session.application.usecase.reward_viewer_time_use_case import RewardViewerTimeUseCase
from app.viewer.session.domain.repository import ViewerRepository
from app.viewer.session.infrastructure.uow.viewer_time_uow import SqlAlchemyViewerTimeUnitOfWorkFactory
from core.types import SessionFactory


class BotManagerFactory:
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        platform_repository: PlatformRepository,
        stream_repository_factory: SessionScopedFactory[StreamRepository],
        minigame_repository: MinigameRepository,
        platform_chat_client: TwitchPlatformChatClient,
        chat_repository_factory: SessionScopedFactory[ChatRepository],
        generate_response_use_case_factory: SessionScopedFactory[GenerateResponseUseCase],
        chat_summary_state: ChatSummaryState,
        conversation_service_factory: SessionScopedFactory[ConversationService],
        jokes_configuration_repository_factory: SessionScopedFactory[JokesConfigurationRepository],
        viewer_repository_factory: SessionScopedFactory[ViewerRepository],
        battle_use_case: BattleUseCase,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        notification_repository: NotificationRepository,
        notification_group_id: int,
        get_used_words_use_case: GetUsedWordsUseCase,
        add_used_words_use_case: AddUsedWordsUseCase,
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        prefix: str,
        guess_number_command_name: str,
        system_prompt_repository_factory: SessionScopedFactory[SystemPromptRepository],
        llm_repository_factory: SessionScopedFactory[LLMRepository],
        command_guess_word: str,
        command_guess_letter: str,
        rps_command_name: str,
        followers_repository_factory: SessionScopedFactory[FollowersRepository],
        platform_auth: PlatformAuth,
        api_client: ApiClient,
        viewer_cache: ViewerCacheService,
        logger: Logger,
    ):
        self._session_factory_rw = session_factory_rw
        self._session_factory_ro = session_factory_ro
        self._platform_repository = platform_repository
        self._stream_repository_factory = stream_repository_factory
        self._minigame_repository = minigame_repository
        self._platform_chat_client = platform_chat_client
        self._chat_repository_factory = chat_repository_factory
        self._generate_response_use_case_factory = generate_response_use_case_factory
        self._chat_summary_state = chat_summary_state
        self._conversation_service_factory = conversation_service_factory
        self._jokes_configuration_repository_factory = jokes_configuration_repository_factory
        self._viewer_repository_factory = viewer_repository_factory
        self._battle_use_case = battle_use_case
        self._economy_policy_factory = economy_policy_factory
        self._notification_repository = notification_repository
        self._notification_group_id = notification_group_id
        self._get_used_words_use_case = get_used_words_use_case
        self._add_used_words_use_case = add_used_words_use_case
        self._get_user_equipment_use_case = get_user_equipment_use_case
        self._prefix = prefix
        self._guess_number_command_name = guess_number_command_name
        self._system_prompt_repository_factory = system_prompt_repository_factory
        self._llm_repository_factory = llm_repository_factory
        self._command_guess_word = command_guess_word
        self._command_guess_letter = command_guess_letter
        self._rps_command_name = rps_command_name
        self._followers_repository_factory = followers_repository_factory
        self._platform_auth = platform_auth
        self._api_client = api_client
        self._viewer_cache = viewer_cache
        self._logger = logger

    def create(self) -> BotManager:
        handle_restore_stream_use_case = HandleRestoreStreamContextUseCase(
            restore_stream_uow=SqlAlchemyRestoreStreamContextUnitOfWorkFactory(
                session_factory_ro=self._session_factory_ro,
                session_factory_rw=self._session_factory_rw,
                stream_repository_factory=self._stream_repository_factory,
            ),
            minigame_repository=self._minigame_repository,
            logger=self._logger,
        )

        chat_use_case_uow_factory = SqlAlchemyChatUseCaseUnitOfWorkFactory(
            session_factory_rw=self._session_factory_rw,
            session_factory_ro=self._session_factory_ro,
            chat_repository_factory=self._chat_repository_factory,
        )
        chat_use_case = ChatUseCase(chat_use_case_uow_factory)
        chat_summarizer_uow_factory = SqlAlchemyChatSummarizerUnitOfWorkFactory(
            session_factory_rw=self._session_factory_rw,
            session_factory_ro=self._session_factory_ro,
            stream_repository_factory=self._stream_repository_factory,
            chat_use_case=chat_use_case,
        )
        handle_chat_summarizer_use_case = HandleChatSummarizerUseCase(
            chat_summarizer_uow=chat_summarizer_uow_factory,
            generate_response_use_case_factory=self._generate_response_use_case_factory,
            session_ro_factory=self._session_factory_ro,
        )
        chat_summarizer_job = ChatSummarizerJob(handle_chat_summarizer_use_case, self._chat_summary_state, self._logger)

        joke_uow_factory = SqlAlchemyJokeUnitOfWorkFactory(
            session_factory_rw=self._session_factory_rw,
            session_factory_ro=self._session_factory_ro,
            conversation_service_factory=self._conversation_service_factory,
            chat_use_case=chat_use_case,
            jokes_configuration_repository_factory=self._jokes_configuration_repository_factory,
        )
        handle_post_joke_use_case = HandlePostJokeUseCase(
            user_cache=viewer_cache,
            platform_repository=self._platform_repository,
            generate_response_use_case_factory=self._generate_response_use_case_factory,
            joke_uow=joke_uow_factory,
            db_ro_session=self._session_factory_ro,
        )
        post_joke_job = PostJokeJob(
            handle_post_joke_use_case=handle_post_joke_use_case,
            send_channel_message=self._platform_chat_client.send_channel_message,
            logger=self._logger,
        )

        handle_token_checker_use_case = HandleTokenCheckerUseCase(
            platform_auth=self._platform_auth,
            logger=self._logger,
        )

        token_checker_job = TokenCheckerJob(handle_token_checker_use_case=handle_token_checker_use_case, logger=self._logger)

        stream_status_uow_factory = SqlAlchemyStreamStatusUnitOfWorkFactory(
            session_factory_rw=self._session_factory_rw,
            session_factory_ro=self._session_factory_ro,
            stream_repository_factory=self._stream_repository_factory,
            viewer_repository_factory=self._viewer_repository_factory,
            battle_use_case=self._battle_use_case,
            economy_policy_factory=self._economy_policy_factory,
            chat_use_case=chat_use_case,
            conversation_service_factory=self._conversation_service_factory,
        )

        handle_stream_status_use_case = HandleStreamStatusUseCase(
            user_cache=viewer_cache,
            platform_repository=self._platform_repository,
            stream_status_uow=stream_status_uow_factory,
            minigame_repository=self._minigame_repository,
            notification_repository=self._notification_repository,
            notification_group_id=self._notification_group_id,
            generate_response_use_case_factory=self._generate_response_use_case_factory,
            state=self._chat_summary_state,
            session_ro_factory=self._session_factory_ro,
            logger=self._logger,
        )

        stream_status_job = StreamStatusJob(handle_stream_status_use_case=handle_stream_status_use_case, logger=self._logger)

        minigame_uow_factory = SqlAlchemyMinigameUnitOfWorkFactory(
            session_factory_rw=self._session_factory_rw,
            session_factory_ro=self._session_factory_ro,
            economy_policy_factory=self._economy_policy_factory,
            chat_use_case=chat_use_case,
            stream_repository_factory=self._stream_repository_factory,
            get_used_words_use_case=self._get_used_words_use_case,
            add_used_words_use_case=self._add_used_words_use_case,
            conversation_service_factory=self._conversation_service_factory,
            get_user_equipment_use_case=self._get_user_equipment_use_case,
        )

        start_number_guess_game_use_case = StartNumberGuessGameUseCase(
            minigame_repository=self._minigame_repository,
            prefix=self._prefix,
            command_name=self._guess_number_command_name,
            send_channel_message=self._platform_chat_client.send_channel_message,
            minigame_uow=minigame_uow_factory,
        )

        start_word_game_use_case = StartWordGameUseCase(
            minigame_repository=self._minigame_repository,
            prefix=self._prefix,
            minigame_uow=minigame_uow_factory,
            db_ro_session=self._session_factory_ro,
            system_prompt_repository_factory=self._system_prompt_repository_factory,
            llm_repository_factory=self._llm_repository_factory,
            command_guess_word=self._command_guess_word,
            command_guess_letter=self._command_guess_letter,
            send_channel_message=self._platform_chat_client.send_channel_message,
            logger=self._logger,
        )

        start_rps_game_use_case = StartRpsGameUseCase(
            minigame_repository=self._minigame_repository,
            prefix=self._prefix,
            command_name=self._rps_command_name,
            send_channel_message=self._platform_chat_client.send_channel_message,
            minigame_uow=minigame_uow_factory,
        )

        finish_rps_game_use_case = FinishRpsUseCase(
            minigame_repository=self._minigame_repository,
            minigame_uow=minigame_uow_factory,
            send_channel_message=self._platform_chat_client.send_channel_message,
        )

        finish_expired_games_use_case = FinishExpiredGamesUseCase(
            minigame_repository=self._minigame_repository,
            send_channel_message=self._platform_chat_client.send_channel_message,
            minigame_uow=minigame_uow_factory,
        )

        handle_minigame_tick_use_case = HandleMinigameTickUseCase(
            minigame_repository=self._minigame_repository,
            minigame_ouw=minigame_uow_factory,
            start_number_guess_game_use_case=start_number_guess_game_use_case,
            start_word_game_use_case=start_word_game_use_case,
            start_rps_game_use_case=start_rps_game_use_case,
            finish_rps_game_use_case=finish_rps_game_use_case,
            finish_expired_games_use_case=finish_expired_games_use_case,
        )

        minigame_job = MinigameTickJob(handle_minigame_tick_use_case=handle_minigame_tick_use_case, logger=self._logger)

        reward_viewer_time_uow_factory = SqlAlchemyViewerTimeUnitOfWorkFactory(
            session_factory_ro=self._session_factory_ro,
            session_factory_rw=self._session_factory_rw,
            stream_repository_factory=self._stream_repository_factory,
            viewer_repository_factory=self._viewer_repository_factory,
            economy_policy_factory=self._economy_policy_factory,
        )
        handle_viewer_time_use_case = RewardViewerTimeUseCase(
            reward_viewer_time_uow=reward_viewer_time_uow_factory,
            user_cache=viewer_cache,
            platform_repository=self._platform_repository,
        )
        viewer_time_job = ViewerTimeJob(handle_viewer_time_use_case=handle_viewer_time_use_case, logger=self._logger)

        sync_followers_uow_factory = SqlAlchemyFollowersSyncUnitOfWorkFactory(
            session_factory_ro=self._session_factory_ro,
            session_factory_rw=self._session_factory_rw,
            followers_repository_factory=self._followers_repository_factory,
        )

        handle_followers_sync_use_case = HandleFollowersSyncUseCase(
            platform_repository=self._platform_repository, sync_followers_uow=sync_followers_uow_factory
        )

        followers_sync_job = FollowersSyncJob(handle_followers_sync_use_case=handle_followers_sync_use_case, logger=self._logger)

        jobs = [
            post_joke_job,
            token_checker_job,
            stream_status_job,
            chat_summarizer_job,
            minigame_job,
            viewer_time_job,
            followers_sync_job,
        ]

        tasks = [Task(job.name, job.run) for job in jobs]

        task_runner = BackgroundTaskRunner(tasks)

        return BotManager(
            logger=self._logger,
            viewer_cache=viewer_cache,
            handle_restore_stream_use_case=handle_restore_stream_use_case,
            platform_chat_client=self._platform_chat_client,
            chat_summarizer_job=chat_summarizer_job,
            post_joke_job=post_joke_job,
            stream_status_job=stream_status_job,
            minigame_job=minigame_job,
            viewer_time_job=viewer_time_job,
            followers_sync_job=followers_sync_job,
            task_runner=task_runner,
            api_client=self._api_client,
        )
