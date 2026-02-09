from __future__ import annotations

from app.ai.gen.application.chat_response_use_case import ChatResponseUseCase
from app.chat.application.chat_summarizer_job import ChatSummarizerJob
from app.chat.application.handle_chat_summarizer_use_case import HandleChatSummarizerUseCase
from app.follow.application.handle_followers_sync_use_case import HandleFollowersSyncUseCase
from app.follow.infrastructure.jobs.followers_sync_job import FollowersSyncJob
from app.joke.application.handle_post_joke_use_case import HandlePostJokeUseCase
from app.joke.application.post_joke_job import PostJokeJob
from app.minigame.application.handle_minigame_tick_use_case import HandleMinigameTickUseCase
from app.minigame.application.minigame_tick_job import MinigameTickJob
from app.platform.application.handle_token_checker_use_case import HandleTokenCheckerUseCase
from app.platform.application.token_checker_job import TokenCheckerJob
from app.platform.auth import PlatformAuth
from app.platform.bot.bot import Bot
from app.platform.bot.bot_settings import BotSettings
from app.stream.application.handle_stream_status_use_case import HandleStreamStatusUseCase
from app.stream.application.stream_status_job import StreamStatusJob
from app.stream.infrastructure.chat_response_adapter import ChatResponseAdapter
from app.stream.infrastructure.telegram_adapter import TelegramNotificationAdapter
from app.viewer.application.handle_viewer_time_use_case import HandleViewerTimeUseCase
from app.viewer.application.viewer_time_job import ViewerTimeJob
from bootstrap.providers_bundle import ProvidersBundle
from bootstrap.uow_composition import UowFactories
from core.background.tasks import BackgroundTasks
from core.chat.outbound import ChatOutbound


def build_background_tasks(
    *,
    providers: ProvidersBundle,
    uow_factories: UowFactories,
    settings: BotSettings,
    bot: Bot,
    chat_response_use_case: ChatResponseUseCase,
    outbound: ChatOutbound,
    platform_auth: PlatformAuth,
) -> BackgroundTasks:
    send_channel_message = outbound.send_channel_message
    notification_port = TelegramNotificationAdapter(providers.telegram_providers.telegram_bot)
    chat_response_port = ChatResponseAdapter(chat_response_use_case)
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
                bot_nick=bot.nick,
            ),
            TokenCheckerJob(
                handle_token_checker_use_case=HandleTokenCheckerUseCase(
                    platform_auth=platform_auth, interval_seconds=1000
                ),
            ),
            StreamStatusJob(
                channel_name=settings.channel_name,
                handle_stream_status_use_case=HandleStreamStatusUseCase(
                    user_cache=providers.user_providers.user_cache,
                    stream_status_port=providers.stream_providers.stream_status_port,
                    unit_of_work_factory=uow_factories.build_stream_status_uow_factory(),
                    minigame_service=providers.minigame_providers.minigame_service,
                    notification_port=notification_port,
                    notification_group_id=settings.group_id,
                    chat_response_port=chat_response_port,
                    state=bot.chat_summary_state,
                ),
                stream_status_interval_seconds=settings.check_stream_status_interval_seconds,
            ),
            ChatSummarizerJob(
                channel_name=settings.channel_name,
                handle_chat_summarizer_use_case=HandleChatSummarizerUseCase(
                    unit_of_work_factory=uow_factories.build_chat_summarizer_uow_factory(),
                    chat_response_use_case=chat_response_use_case,
                ),
                chat_summary_state=bot.chat_summary_state,
            ),
            MinigameTickJob(
                channel_name=settings.channel_name,
                handle_minigame_tick_use_case=HandleMinigameTickUseCase(
                    minigame_orchestrator=bot.minigame_orchestrator,
                ),
            ),
            ViewerTimeJob(
                channel_name=settings.channel_name,
                handle_viewer_time_use_case=HandleViewerTimeUseCase(
                    unit_of_work_factory=uow_factories.build_viewer_time_uow_factory(),
                    user_cache=providers.user_providers.user_cache,
                    stream_chatters_port=providers.stream_providers.stream_chatters_port,
                ),
                bot_nick=bot.nick,
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
