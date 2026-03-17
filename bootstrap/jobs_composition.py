from __future__ import annotations

from app.ai.gen.application.use_cases.chat_response_use_case import ChatResponseUseCase
from app.chat.application.job.chat_summarizer_job import ChatSummarizerJob
from app.chat.application.model.chat_summary_state import ChatSummaryState
from app.chat.application.usecase.handle_chat_summarizer_use_case import HandleChatSummarizerUseCase
from app.follow.application.usecases.handle_followers_sync_use_case import HandleFollowersSyncUseCase
from app.follow.infrastructure.jobs.followers_sync_job import FollowersSyncJob
from app.joke.application.job.post_joke_job import PostJokeJob
from app.joke.application.usecase.handle_post_joke_use_case import HandlePostJokeUseCase
from app.minigame.application.job.minigame_tick_job import MinigameTickJob
from app.minigame.application.use_case.finish_expired_games_use_case import FinishExpiredGamesUseCase
from app.minigame.application.use_case.finish_rps_use_case import FinishRpsUseCase
from app.minigame.application.use_case.handle_minigame_tick_use_case import HandleMinigameTickUseCase
from app.minigame.application.use_case.start_number_guess_game_use_case import StartNumberGuessGameUseCase
from app.minigame.application.use_case.start_rps_game_use_case import StartRpsGameUseCase
from app.minigame.application.use_case.start_word_game_use_case import StartWordGameUseCase
from app.notification.infrastructure.repository import NotificationRepositoryImpl
from app.platform.application.handle_token_checker_use_case import HandleTokenCheckerUseCase
from app.platform.application.token_checker_job import TokenCheckerJob
from app.platform.auth.platform_auth import PlatformAuth
from app.platform.bot.model.bot_settings import BotSettings
from app.platform.domain.repository import PlatformRepository
from app.stream.application.job.stream_status_job import StreamStatusJob
from app.stream.application.usecase.handle_stream_status_use_case import HandleStreamStatusUseCase
from app.stream.infrastructure.adapters.generate_stream_info_adapter import GenerateStreamInfoAdapter
from app.viewer.application.jobs.viewer_time_job import ViewerTimeJob
from app.viewer.application.usecases.reward_viewer_time_use_case import RewardViewerTimeUseCase
from bootstrap.providers_bundle import ProvidersBundle
from bootstrap.uow_composition import UowFactories
from core.background.tasks import BackgroundTasks
from core.chat.outbound import ChatOutbound
from core.db import db_ro_session


def build_background_tasks(
    providers: ProvidersBundle,
    uow_factories: UowFactories,
    settings: BotSettings,
    bot_name: str,
    chat_summary_state: ChatSummaryState,
    chat_response_use_case: ChatResponseUseCase,
    outbound: ChatOutbound,
    platform_auth: PlatformAuth,
    platform_repository: PlatformRepository,
) -> BackgroundTasks:
    send_channel_message = outbound.send_channel_message
    notifications_port = NotificationRepositoryImpl(providers.telegram_providers.telegram_bot)
    chat_response_port = GenerateStreamInfoAdapter(chat_response_use_case)
    return BackgroundTasks(
        runner=providers.background_providers.runner,
        jobs=[
            PostJokeJob(
                channel_name=settings.channel_name,
                handle_post_joke_use_case=HandlePostJokeUseCase(
                    joke_service=providers.joke_providers.joke_service,
                    user_cache=providers.user_providers.user_cache,
                    platform_repository=platform_repository,
                    chat_response_use_case=chat_response_use_case,
                    unit_of_work_factory=uow_factories.build_joke_uow_factory(),
                ),
                send_channel_message=send_channel_message,
                bot_nick=bot_name,
            ),
            TokenCheckerJob(
                handle_token_checker_use_case=HandleTokenCheckerUseCase(platform_auth=platform_auth),
            ),
            StreamStatusJob(
                channel_name=settings.channel_name,
                handle_stream_status_use_case=HandleStreamStatusUseCase(
                    user_cache=providers.user_providers.user_cache,
                    platform_repository=platform_repository,
                    unit_of_work_factory=uow_factories.build_stream_status_uow_factory(),
                    minigame_repository=providers.minigame_providers.minigame_repository,
                    notification_repository=notifications_port,
                    notification_group_id=settings.group_id,
                    chat_response_port=chat_response_port,
                    state=chat_summary_state,
                ),
            ),
            ChatSummarizerJob(
                channel_name=settings.channel_name,
                handle_chat_summarizer_use_case=HandleChatSummarizerUseCase(
                    unit_of_work_factory=uow_factories.build_chat_summarizer_uow_factory(),
                    chat_response_use_case=chat_response_use_case,
                ),
                chat_summary_state=chat_summary_state,
            ),
            MinigameTickJob(
                channel_name=settings.channel_name,
                handle_minigame_tick_use_case=HandleMinigameTickUseCase(
                    minigame_repository=providers.minigame_providers.minigame_repository,
                    minigame_ouw=uow_factories.build_minigame_uow_factory(),
                    start_number_guess_game_use_case=StartNumberGuessGameUseCase(
                        minigame_repository=providers.minigame_providers.minigame_repository,
                        prefix=settings.prefix,
                        command_name=settings.command_guess,
                        send_channel_message=send_channel_message,
                        minigame_uow=uow_factories.build_minigame_uow_factory(),
                        bot_name=settings.bot_name.lower(),
                    ),
                    start_word_game_use_case=StartWordGameUseCase(
                        minigame_repository=providers.minigame_providers.minigame_repository,
                        prefix=settings.prefix,
                        minigame_uow=uow_factories.build_minigame_uow_factory(),
                        db_ro_session=db_ro_session,
                        system_prompt_repository_provider=providers.ai_providers.system_prompt_repo_provider,
                        llm_repository=providers.ai_providers.llm_repository,
                        command_guess_word=settings.command_guess_word,
                        command_guess_letter=settings.command_guess_letter,
                        send_channel_message=send_channel_message,
                        bot_name=settings.bot_name.lower(),
                    ),
                    start_rps_game_use_case=StartRpsGameUseCase(
                        minigame_repository=providers.minigame_providers.minigame_repository,
                        prefix=settings.prefix,
                        command_name=settings.command_rps,
                        send_channel_message=send_channel_message,
                        minigame_uow=uow_factories.build_minigame_uow_factory(),
                        bot_name=settings.bot_name.lower(),
                    ),
                    finish_rps_game_use_case=FinishRpsUseCase(
                        minigame_repository=providers.minigame_providers.minigame_repository,
                        minigame_uow=uow_factories.build_minigame_uow_factory(),
                        bot_name=settings.bot_name.lower(),
                        send_channel_message=send_channel_message,
                    ),
                    finish_expired_games_use_case=FinishExpiredGamesUseCase(
                        minigame_repository=providers.minigame_providers.minigame_repository,
                        send_channel_message=send_channel_message,
                        minigame_uow=uow_factories.build_minigame_uow_factory(),
                        bot_name=settings.bot_name.lower(),
                    ),
                ),
            ),
            ViewerTimeJob(
                channel_name=settings.channel_name,
                handle_viewer_time_use_case=RewardViewerTimeUseCase(
                    reward_viewer_time_uow=uow_factories.build_viewer_time_uow_factory(),
                    user_cache=providers.user_providers.user_cache,
                    platform_repository=platform_repository,
                ),
                bot_nick=bot_name,
            ),
            FollowersSyncJob(
                channel_name=settings.channel_name,
                handle_followers_sync_use_case=HandleFollowersSyncUseCase(
                    platform_repository=platform_repository,
                    sync_followers_uow=uow_factories.build_followers_sync_uow_factory(),
                ),
            ),
        ],
    )
