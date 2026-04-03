from __future__ import annotations

from collections.abc import Awaitable, Callable

from app.ai.gen.application.use_cases.generate_response_use_case import GenerateResponseUseCase
from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.chat.application.job.chat_summarizer_job import ChatSummarizerJob
from app.chat.application.model.chat_summary_state import ChatSummaryState
from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.chat.application.usecase.handle_chat_summarizer_use_case import HandleChatSummarizerUseCase
from app.core.logger.domain.logger import Logger
from app.follow.application.usecases.handle_followers_sync_use_case import HandleFollowersSyncUseCase
from app.follow.infrastructure.jobs.followers_sync_job import FollowersSyncJob
from app.joke.di.dependencies import (
    provide_handle_post_joke_use_case,
    provide_joke_service,
    provide_joke_settings_repository,
    provide_joke_unit_of_work_factory,
    provide_post_joke_job,
)
from app.minigame.application.job.minigame_tick_job import MinigameTickJob
from app.minigame.application.use_case.finish_expired_games_use_case import FinishExpiredGamesUseCase
from app.minigame.application.use_case.finish_rps_use_case import FinishRpsUseCase
from app.minigame.application.use_case.handle_minigame_tick_use_case import HandleMinigameTickUseCase
from app.minigame.application.use_case.start_number_guess_game_use_case import StartNumberGuessGameUseCase
from app.minigame.application.use_case.start_rps_game_use_case import StartRpsGameUseCase
from app.minigame.application.use_case.start_word_game_use_case import StartWordGameUseCase
from app.notification.di.dependencies import provide_notification_repository, provide_telegram_bot
from app.platform.auth.application.di.dependencies import provide_handle_token_checker_use_case, provide_token_checker_job
from app.platform.auth.platform_auth import PlatformAuth
from app.platform.bot.model.bot_settings import BotSettings
from app.platform.domain.repository import PlatformRepository
from app.stream.di.dependencies import provide_handle_stream_status_use_case, provide_stream_status_job
from app.stream.infrastructure.adapters.generate_stream_info_adapter import GenerateStreamInfoAdapter
from app.user.application.ports.user_cache_port import UserCachePort
from app.viewer.application.jobs.viewer_time_job import ViewerTimeJob
from app.viewer.application.usecases.reward_viewer_time_use_case import RewardViewerTimeUseCase
from bootstrap.providers_bundle import ProvidersBundle
from bootstrap.uow_composition import UowFactories
from core.background.task_runner import BackgroundTaskRunner
from core.background.tasks import BackgroundTasks
from core.db import db_ro_session
from core.provider import Provider
from core.types import SessionFactory


def build_background_tasks(
    providers: ProvidersBundle,
    uow_factories: UowFactories,
    settings: BotSettings,
    bot_name: str,
    chat_summary_state: ChatSummaryState,
    chat_response_use_case: GenerateResponseUseCase,
    send_channel_message: Callable[[str], Awaitable[None]],
    platform_auth: PlatformAuth,
    platform_repository: PlatformRepository,
    logger: Logger,
    user_cache: UserCachePort,
    session_factory_rw: SessionFactory,
    session_factory_ro: SessionFactory,
    conversation_service_provider: Provider[ConversationService],
    chat_use_case_provider: Provider[ChatUseCase],
    tg_bot_token: str,
    channel_name: str,
) -> BackgroundTasks:
    telegram_bot = provide_telegram_bot(tg_bot_token)
    notifications_repository = provide_notification_repository(telegram_bot)
    chat_response_port = GenerateStreamInfoAdapter(chat_response_use_case)
    joke_repository = provide_joke_settings_repository(logger)
    return BackgroundTasks(
        runner=BackgroundTaskRunner(),
        jobs=[
            provide_post_joke_job(
                channel_name=channel_name,
                handle_post_joke_use_case=provide_handle_post_joke_use_case(
                    joke_service=provide_joke_service(joke_repository, logger),
                    user_cache=user_cache,
                    platform_repository=platform_repository,
                    generate_response_use_case=chat_response_use_case,
                    joke_uow_factory=provide_joke_unit_of_work_factory(
                        session_factory_rw=session_factory_rw,
                        session_factory_ro=session_factory_ro,
                        conversation_service_provider=conversation_service_provider,
                        chat_use_case_provider=chat_use_case_provider,
                    ),
                ),
                send_channel_message=send_channel_message,
                bot_name=bot_name,
                logger=logger,
            ),
            provide_token_checker_job(
                handle_token_checker_use_case=provide_handle_token_checker_use_case(platform_auth, logger), logger=logger
            ),
            provide_stream_status_job(
                channel_name=channel_name,
                handle_stream_status_use_case=provide_handle_stream_status_use_case(
                    user_cache=user_cache,
                    platform_repository=platform_repository,
                    stream_status_uow_factory=uow_factories.build_stream_status_uow_factory(),
                    minigame_repository=providers.minigame_providers.minigame_repository,
                    notification_repository=notifications_repository,
                    notification_group_id=settings.group_id,
                    chat_response_port=chat_response_port,
                    state=chat_summary_state,
                    logger=logger,
                ),
                logger=logger,
            ),
            ChatSummarizerJob(
                channel_name=channel_name,
                handle_chat_summarizer_use_case=HandleChatSummarizerUseCase(
                    unit_of_work_factory=uow_factories.build_chat_summarizer_uow_factory(),
                    chat_response_use_case=chat_response_use_case,
                ),
                chat_summary_state=chat_summary_state,
            ),
            MinigameTickJob(
                channel_name=channel_name,
                handle_minigame_tick_use_case=HandleMinigameTickUseCase(
                    minigame_repository=providers.minigame_providers.minigame_repository,
                    minigame_ouw=uow_factories.build_minigame_uow_factory(),
                    start_number_guess_game_use_case=StartNumberGuessGameUseCase(
                        minigame_repository=providers.minigame_providers.minigame_repository,
                        prefix=settings.prefix,
                        command_name=settings.command_guess,
                        send_channel_message=send_channel_message,
                        minigame_uow=uow_factories.build_minigame_uow_factory(),
                        bot_name=bot_name.lower(),
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
                        bot_name=bot_name.lower(),
                    ),
                    start_rps_game_use_case=StartRpsGameUseCase(
                        minigame_repository=providers.minigame_providers.minigame_repository,
                        prefix=settings.prefix,
                        command_name=settings.command_rps,
                        send_channel_message=send_channel_message,
                        minigame_uow=uow_factories.build_minigame_uow_factory(),
                        bot_name=bot_name.lower(),
                    ),
                    finish_rps_game_use_case=FinishRpsUseCase(
                        minigame_repository=providers.minigame_providers.minigame_repository,
                        minigame_uow=uow_factories.build_minigame_uow_factory(),
                        bot_name=bot_name.lower(),
                        send_channel_message=send_channel_message,
                    ),
                    finish_expired_games_use_case=FinishExpiredGamesUseCase(
                        minigame_repository=providers.minigame_providers.minigame_repository,
                        send_channel_message=send_channel_message,
                        minigame_uow=uow_factories.build_minigame_uow_factory(),
                        bot_name=bot_name.lower(),
                    ),
                ),
                logger=logger,
            ),
            ViewerTimeJob(
                channel_name=channel_name,
                handle_viewer_time_use_case=RewardViewerTimeUseCase(
                    reward_viewer_time_uow=uow_factories.build_viewer_time_uow_factory(),
                    user_cache=user_cache,
                    platform_repository=platform_repository,
                ),
                bot_nick=bot_name,
                logger=logger,
            ),
            FollowersSyncJob(
                channel_name=channel_name,
                handle_followers_sync_use_case=HandleFollowersSyncUseCase(
                    platform_repository=platform_repository,
                    sync_followers_uow=uow_factories.build_followers_sync_uow_factory(),
                ),
                logger=logger,
            ),
        ],
    )
