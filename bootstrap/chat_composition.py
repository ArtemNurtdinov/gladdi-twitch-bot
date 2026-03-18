from __future__ import annotations

from collections.abc import Awaitable, Callable

from app.ai.gen.application.use_cases.chat_response_use_case import ChatResponseUseCase
from app.commands.chat.application.handle_chat_message_use_case import HandleChatMessageUseCase
from app.commands.chat.infrastructure.chat_event_handler import ChatEventsHandlerImpl
from bootstrap.providers_bundle import ProvidersBundle
from bootstrap.uow_composition import UowFactories


def build_chat_event_handler(
    providers: ProvidersBundle,
    uow_factories: UowFactories,
    chat_response_use_case: ChatResponseUseCase,
    send_channel_message: Callable[[str], Awaitable[None]],
) -> ChatEventsHandlerImpl:
    handle_chat_message = HandleChatMessageUseCase(
        unit_of_work_factory=uow_factories.build_chat_message_uow_factory(),
        get_intent_from_text_use_case=providers.ai_providers.get_intent_use_case,
        prompt_service=providers.ai_providers.prompt_service,
        chat_response_use_case=chat_response_use_case,
    )
    return ChatEventsHandlerImpl(
        handle_chat_message_use_case=handle_chat_message,
        send_channel_message=send_channel_message,
    )
