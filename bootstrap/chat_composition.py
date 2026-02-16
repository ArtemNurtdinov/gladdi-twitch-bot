from __future__ import annotations

from app.ai.gen.application.chat_response_use_case import ChatResponseUseCase
from app.ai.gen.prompt.prompt_service import PromptService
from app.commands.chat.application.handle_chat_message_use_case import HandleChatMessageUseCase
from app.commands.chat.presentation.chat_event_handler import DefaultChatEventsHandler
from app.minigame.application.minigame_orchestrator import MinigameOrchestrator
from app.platform.bot.bot import Bot
from app.platform.bot.bot_settings import BotSettings
from bootstrap.providers_bundle import ProvidersBundle
from bootstrap.uow_composition import UowFactories
from core.chat.outbound import ChatOutbound


def build_chat_event_handler(
    *,
    providers: ProvidersBundle,
    uow_factories: UowFactories,
    prompt_service: PromptService,
    chat_response_use_case: ChatResponseUseCase,
    outbound: ChatOutbound,
) -> DefaultChatEventsHandler:
    handle_chat_message = HandleChatMessageUseCase(
        unit_of_work_factory=uow_factories.build_chat_message_uow_factory(),
        get_intent_from_text_use_case=providers.ai_providers.get_intent_use_case,
        prompt_service=providers.ai_providers.prompt_service,
        chat_response_use_case=chat_response_use_case,
    )
    return DefaultChatEventsHandler(
        handle_chat_message_use_case=handle_chat_message,
        send_channel_message=outbound.send_channel_message,
    )


def build_minigame(
    *,
    providers: ProvidersBundle,
    uow_factories: UowFactories,
    settings: BotSettings,
    bot: Bot,
    prompt_service: PromptService,
    outbound: ChatOutbound,
) -> MinigameOrchestrator:
    return MinigameOrchestrator(
        minigame_service=providers.minigame_providers.minigame_service,
        unit_of_work_factory=uow_factories.build_minigame_uow_factory(),
        llm_client=providers.ai_providers.llm_client,
        prompt_service=prompt_service,
        prefix=settings.prefix,
        command_guess_letter=settings.command_guess_letter,
        command_guess_word=settings.command_guess_word,
        command_guess=settings.command_guess,
        command_rps=settings.command_rps,
        bot_nick=bot.nick,
        send_channel_message=outbound.send_channel_message,
    )
