from collections.abc import Callable
from dataclasses import dataclass

from app.ai.bootstrap import build_ai_providers
from app.ai.gen.application.chat_response_use_case import ChatResponseUseCase
from app.battle.bootstrap import build_battle_providers
from app.betting.bootstrap import build_betting_providers
from app.chat.application.chat_summarizer_job import ChatSummarizerJob
from app.chat.application.handle_chat_summarizer_use_case import HandleChatSummarizerUseCase
from app.chat.bootstrap import build_chat_providers
from app.commands.application.commands_registry import CommandRegistryProtocol
from app.commands.chat.application.handle_chat_message_use_case import HandleChatMessageUseCase
from app.commands.chat.presentation.chat_event_handler import DefaultChatEventsHandler
from app.economy.bootstrap import build_economy_providers
from app.equipment.bootstrap import build_equipment_providers
from app.follow.application.handle_followers_sync_use_case import HandleFollowersSyncUseCase
from app.follow.bootstrap import build_follow_providers
from app.follow.infrastructure.jobs.followers_sync_job import FollowersSyncJob
from app.joke.application.handle_post_joke_use_case import HandlePostJokeUseCase
from app.joke.application.post_joke_job import PostJokeJob
from app.joke.bootstrap import build_joke_providers
from app.minigame.application.handle_minigame_tick_use_case import HandleMinigameTickUseCase
from app.minigame.application.handle_rps_use_case import HandleRpsUseCase
from app.minigame.application.minigame_orchestrator import MinigameOrchestrator
from app.minigame.application.minigame_tick_job import MinigameTickJob
from app.minigame.bootstrap import build_minigame_providers
from app.platform.application.handle_token_checker_use_case import HandleTokenCheckerUseCase
from app.platform.application.token_checker_job import TokenCheckerJob
from app.platform.auth import PlatformAuth
from app.platform.bot.bot import Bot
from app.platform.bot.bot_settings import BotSettings
from app.platform.providers import PlatformProviders
from app.stream.application.handle_restore_stream_context_use_case import HandleRestoreStreamContextUseCase
from app.stream.application.handle_stream_status_use_case import HandleStreamStatusUseCase
from app.stream.application.model import RestoreStreamJobDTO
from app.stream.application.stream_status_job import StreamStatusJob
from app.stream.bootstrap import build_stream_providers
from app.stream.infrastructure.chat_response_adapter import ChatResponseAdapter
from app.stream.infrastructure.telegram_adapter import TelegramNotificationAdapter
from app.user.bootstrap import build_user_providers
from app.viewer.application.handle_viewer_time_use_case import HandleViewerTimeUseCase
from app.viewer.application.viewer_time_job import ViewerTimeJob
from app.viewer.bootstrap import build_viewer_providers
from bootstrap.commands_composition import build_command_registry
from bootstrap.providers_bundle import ProvidersBundle
from bootstrap.telegram_provider import build_telegram_providers
from bootstrap.uow_composition import create_uow_factories
from core.background.tasks import BackgroundTasks
from core.bootstrap.background import build_background_providers
from core.chat.interfaces import CommandRouter
from core.chat.outbound import ChatOutbound
from core.db import db_ro_session, db_rw_session


@dataclass
class BotComposition:
    bot: Bot
    chat_client: ChatOutbound
    platform_providers: PlatformProviders


async def build_bot_composition(
    *,
    access_token: str,
    refresh_token: str,
    tg_bot_token: str,
    llmbox_host: str,
    intent_detector_host: str,
    client_id: str,
    client_secret: str,
    settings: BotSettings,
    platform_auth_factory: Callable[[str, str, str, str], PlatformAuth],
    platform_providers_builder: Callable[[PlatformAuth], PlatformProviders],
    chat_client_factory: Callable[[PlatformAuth, BotSettings, str | None], ChatOutbound],
    command_router_builder: Callable[[BotSettings, CommandRegistryProtocol, Bot], CommandRouter],
) -> BotComposition:
    auth = platform_auth_factory(access_token, refresh_token, client_id, client_secret)
    platform_providers = platform_providers_builder(auth)
    streaming_platform = platform_providers.streaming_platform

    stream_providers = build_stream_providers(streaming_platform)
    ai_providers = build_ai_providers(llmbox_host=llmbox_host, intent_detector_host=intent_detector_host)
    chat_providers = build_chat_providers()
    follow_providers = build_follow_providers(streaming_platform)
    joke_providers = build_joke_providers()
    user_providers = build_user_providers(streaming_platform)
    viewer_providers = build_viewer_providers()
    economy_providers = build_economy_providers()
    equipment_providers = build_equipment_providers()
    minigame_providers = build_minigame_providers()
    battle_providers = build_battle_providers()
    betting_providers = build_betting_providers()
    background_providers = build_background_providers()
    telegram_providers = build_telegram_providers(tg_bot_token=tg_bot_token)

    providers_bundle = ProvidersBundle(
        ai_providers=ai_providers,
        stream_providers=stream_providers,
        chat_providers=chat_providers,
        follow_providers=follow_providers,
        joke_providers=joke_providers,
        user_providers=user_providers,
        viewer_providers=viewer_providers,
        economy_providers=economy_providers,
        equipment_providers=equipment_providers,
        minigame_providers=minigame_providers,
        battle_providers=battle_providers,
        betting_providers=betting_providers,
        background_providers=background_providers,
        telegram_providers=telegram_providers,
    )
    uow_factories = create_uow_factories(
        session_factory_rw=db_rw_session,
        session_factory_ro=db_ro_session,
        providers=providers_bundle,
    )

    bot_user = await streaming_platform.get_user_by_login(settings.bot_name)
    bot_user_id = bot_user.id if bot_user else None
    chat_client = chat_client_factory(platform_providers.platform_auth, settings, bot_user_id)

    def build_chat_response_use_case(system_prompt: str) -> ChatResponseUseCase:
        return ChatResponseUseCase(
            unit_of_work_factory=uow_factories.build_chat_response_uow_factory(),
            llm_client=ai_providers.llm_client,
            system_prompt=system_prompt,
        )

    def build_minigame(bot: Bot, system_prompt: str, outbound: ChatOutbound) -> MinigameOrchestrator:
        return MinigameOrchestrator(
            minigame_service=minigame_providers.minigame_service,
            unit_of_work_factory=uow_factories.build_minigame_uow_factory(),
            llm_client=ai_providers.llm_client,
            system_prompt=system_prompt,
            prefix=settings.prefix,
            command_guess_letter=settings.command_guess_letter,
            command_guess_word=settings.command_guess_word,
            command_guess=settings.command_guess,
            command_rps=settings.command_rps,
            bot_nick=bot.nick,
            send_channel_message=outbound.send_channel_message,
        )

    def build_background_tasks(bot: Bot, chat_response_use_case: ChatResponseUseCase, outbound: ChatOutbound) -> BackgroundTasks:
        send_channel_message = outbound.send_channel_message
        notification_port = TelegramNotificationAdapter(telegram_providers.telegram_bot)
        chat_response_port = ChatResponseAdapter(chat_response_use_case)
        return BackgroundTasks(
            runner=background_providers.runner,
            jobs=[
                PostJokeJob(
                    channel_name=settings.channel_name,
                    handle_post_joke_use_case=HandlePostJokeUseCase(
                        joke_service=joke_providers.joke_service,
                        user_cache=user_providers.user_cache,
                        stream_info=stream_providers.stream_info_port,
                        chat_response_use_case=chat_response_use_case,
                        unit_of_work_factory=uow_factories.build_joke_uow_factory(),
                    ),
                    send_channel_message=send_channel_message,
                    bot_nick=bot.nick,
                ),
                TokenCheckerJob(
                    handle_token_checker_use_case=HandleTokenCheckerUseCase(
                        platform_auth=platform_providers.platform_auth, interval_seconds=1000
                    ),
                ),
                StreamStatusJob(
                    channel_name=settings.channel_name,
                    handle_stream_status_use_case=HandleStreamStatusUseCase(
                        user_cache=user_providers.user_cache,
                        stream_status_port=stream_providers.stream_status_port,
                        unit_of_work_factory=uow_factories.build_stream_status_uow_factory(),
                        minigame_service=minigame_providers.minigame_service,
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
                        user_cache=user_providers.user_cache,
                        stream_chatters_port=stream_providers.stream_chatters_port,
                    ),
                    bot_nick=bot.nick,
                    check_interval_seconds=settings.check_viewers_interval_seconds,
                ),
                FollowersSyncJob(
                    channel_name=settings.channel_name,
                    handle_followers_sync_use_case=HandleFollowersSyncUseCase(
                        followers_port=follow_providers.followers_port,
                        unit_of_work_factory=uow_factories.build_followers_sync_uow_factory(),
                    ),
                    interval_seconds=settings.sync_followers_interval_seconds,
                ),
            ],
        )

    def build_chat_event_handler(
        chat_response_use_case: ChatResponseUseCase, system_prompt: str, outbound: ChatOutbound
    ) -> DefaultChatEventsHandler:
        handle_chat_message = HandleChatMessageUseCase(
            unit_of_work_factory=uow_factories.build_chat_message_uow_factory(),
            get_intent_from_text_use_case=ai_providers.get_intent_use_case,
            prompt_service=ai_providers.prompt_service,
            system_prompt=system_prompt,
            chat_response_use_case=chat_response_use_case,
        )
        return DefaultChatEventsHandler(
            handle_chat_message_use_case=handle_chat_message,
            send_channel_message=outbound.send_channel_message,
        )

    def restore_stream_context() -> None:
        if not settings.channel_name:
            return
        restore_stream_job_dto = RestoreStreamJobDTO(settings.channel_name)
        HandleRestoreStreamContextUseCase(
            unit_of_work_factory=uow_factories.build_restore_stream_context_uow_factory(),
            minigame_service=minigame_providers.minigame_service,
        ).handle(restore_stream_job_dto)

    bot = Bot(platform_providers, user_providers, settings)
    system_prompt = ai_providers.prompt_service.get_system_prompt_for_group()
    chat_response_use_case = build_chat_response_use_case(system_prompt)

    bot.set_minigame_orchestrator(build_minigame(bot, system_prompt, chat_client))
    bot.set_background_tasks(build_background_tasks(bot, chat_response_use_case, chat_client))
    command_registry = build_command_registry(
        providers=providers_bundle,
        uow_factories=uow_factories,
        settings=settings,
        bot=bot,
        chat_response_use_case=chat_response_use_case,
        system_prompt=system_prompt,
        streaming_platform=platform_providers.streaming_platform,
        outbound=chat_client,
    )
    chat_client.set_chat_event_handler(build_chat_event_handler(chat_response_use_case, system_prompt, chat_client))
    chat_client.set_router(command_router_builder(settings, command_registry, bot))
    restore_stream_context()

    return BotComposition(bot=bot, chat_client=chat_client, platform_providers=platform_providers)
