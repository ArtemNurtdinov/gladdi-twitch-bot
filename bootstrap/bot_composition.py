from collections.abc import Callable
from dataclasses import dataclass

from app.ai.gen.application.chat_response_use_case import ChatResponseUseCase
from app.commands.application.commands_registry import CommandRegistryProtocol
from app.platform.auth import PlatformAuth
from app.platform.bot.bot import Bot
from app.platform.bot.bot_settings import BotSettings
from app.platform.providers import PlatformProviders
from bootstrap.chat_composition import build_chat_event_handler, build_minigame
from bootstrap.commands_composition import build_command_registry
from bootstrap.jobs_composition import build_background_tasks
from bootstrap.providers_bundle import build_providers_bundle
from bootstrap.stream_composition import restore_stream_context
from bootstrap.uow_composition import create_uow_factories
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

    providers_bundle = build_providers_bundle(
        streaming_platform=streaming_platform,
        tg_bot_token=tg_bot_token,
        llmbox_host=llmbox_host,
        intent_detector_host=intent_detector_host,
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
            llm_client=providers_bundle.ai_providers.llm_client,
            system_prompt=system_prompt,
        )

    bot = Bot(platform_providers, providers_bundle.user_providers, settings)
    system_prompt = providers_bundle.ai_providers.prompt_service.get_system_prompt_for_group()
    chat_response_use_case = build_chat_response_use_case(system_prompt)

    bot.set_minigame_orchestrator(
        build_minigame(
            providers=providers_bundle,
            uow_factories=uow_factories,
            settings=settings,
            bot=bot,
            system_prompt=system_prompt,
            outbound=chat_client,
        )
    )
    bot.set_background_tasks(
        build_background_tasks(
            providers=providers_bundle,
            uow_factories=uow_factories,
            settings=settings,
            bot=bot,
            chat_response_use_case=chat_response_use_case,
            outbound=chat_client,
            platform_auth=platform_providers.platform_auth,
        )
    )
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
    chat_client.set_chat_event_handler(
        build_chat_event_handler(
            providers=providers_bundle,
            uow_factories=uow_factories,
            system_prompt=system_prompt,
            chat_response_use_case=chat_response_use_case,
            outbound=chat_client,
        )
    )
    chat_client.set_router(command_router_builder(settings, command_registry, bot))
    restore_stream_context(
        providers=providers_bundle,
        uow_factories=uow_factories,
        settings=settings,
    )

    return BotComposition(bot=bot, chat_client=chat_client, platform_providers=platform_providers)
