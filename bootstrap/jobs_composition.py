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
from app.minigame.application.minigame_orchestrator import MinigameOrchestrator
from app.minigame.application.use_case.handle_minigame_tick_use_case import HandleMinigameTickUseCase
from app.platform.application.handle_token_checker_use_case import HandleTokenCheckerUseCase
from app.platform.application.token_checker_job import TokenCheckerJob
from app.platform.auth import PlatformAuth
from app.platform.bot.model.bot_settings import BotSettings
from app.stream.application.job.stream_status_job import StreamStatusJob
from app.stream.application.usecase.handle_stream_status_use_case import HandleStreamStatusUseCase
from app.stream.infrastructure.adapters.generate_stream_info_adapter import GenerateStreamInfoAdapter
from app.stream.infrastructure.adapters.telegram_notification_adapter import TelegramNotificationAdapter
from app.viewer.application.jobs.viewer_time_job import ViewerTimeJob
from app.viewer.application.usecases.reward_viewer_time_use_case import RewardViewerTimeUseCase
from bootstrap.providers_bundle import ProvidersBundle
from bootstrap.uow_composition import UowFactories
from core.background.tasks import BackgroundTasks
from core.chat.outbound import ChatOutbound


def build_background_tasks(
    providers: ProvidersBundle,
    uow_factories: UowFactories,
    settings: BotSettings,
    bot_name: str,
    chat_summary_state: ChatSummaryState,
    minigame_orchestrator: MinigameOrchestrator,
    chat_response_use_case: ChatResponseUseCase,
    outbound: ChatOutbound,
    platform_auth: PlatformAuth,
) -> BackgroundTasks:
    send_channel_message = outbound.send_channel_message
    notifications_port = TelegramNotificationAdapter(providers.telegram_providers.telegram_bot)
    chat_response_port = GenerateStreamInfoAdapter(chat_response_use_case)
    return BackgroundTasks(
        runner=providers.background_providers.runner,
        jobs=[
            PostJokeJob(
                channel_name=settings.channel_name,
                handle_post_joke_use_case=HandlePostJokeUseCase(
                    joke_service=providers.joke_providers.joke_service,
                    user_cache=providers.user_providers.user_cache,
                    stream_info=providers.stream_providers.stream_info_port,
                    chat_response_use_case=chat_response_use_case,
                    unit_of_work_factory=uow_factories.build_joke_uow_factory(),
                ),
                send_channel_message=send_channel_message,
                bot_nick=bot_name,
            ),
            TokenCheckerJob(
                handle_token_checker_use_case=HandleTokenCheckerUseCase(platform_auth=platform_auth, interval_seconds=1000),
            ),
            StreamStatusJob(
                channel_name=settings.channel_name,
                handle_stream_status_use_case=HandleStreamStatusUseCase(
                    user_cache=providers.user_providers.user_cache,
                    stream_status_port=providers.stream_providers.stream_status_port,
                    unit_of_work_factory=uow_factories.build_stream_status_uow_factory(),
                    minigame_service=providers.minigame_providers.minigame_service,
                    notifications_port=notifications_port,
                    notification_group_id=settings.group_id,
                    chat_response_port=chat_response_port,
                    state=chat_summary_state,
                ),
                stream_status_interval_seconds=settings.check_stream_status_interval_seconds,
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
                    minigame_orchestrator=minigame_orchestrator,
                ),
            ),
            ViewerTimeJob(
                channel_name=settings.channel_name,
                handle_viewer_time_use_case=RewardViewerTimeUseCase(
                    reward_viewer_time_uow=uow_factories.build_viewer_time_uow_factory(),
                    user_cache=providers.user_providers.user_cache,
                    stream_chatters_port=providers.stream_providers.stream_chatters_port,
                ),
                bot_nick=bot_name,
                check_interval_seconds=settings.check_viewers_interval_seconds,
            ),
            FollowersSyncJob(
                channel_name=settings.channel_name,
                handle_followers_sync_use_case=HandleFollowersSyncUseCase(
                    followers_port=providers.follow_providers.followers_port,
                    unit_of_work_factory=uow_factories.build_followers_sync_uow_factory(),
                ),
                interval_seconds=settings.sync_followers_interval_seconds,
            ),
        ],
    )
