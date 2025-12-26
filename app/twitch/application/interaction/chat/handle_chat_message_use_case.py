from typing import Callable, ContextManager, Optional

from sqlalchemy.orm import Session

from app.ai.application.intent_use_case import IntentUseCase
from app.ai.application.prompt_service import PromptService
from app.ai.domain.models import Intent
from app.twitch.application.interaction.chat.dto import ChatMessageDTO
from app.twitch.application.shared import StreamServiceProvider
from app.twitch.application.shared.chat_use_case_provider import ChatUseCaseProvider
from app.twitch.application.shared.economy_service_provider import EconomyServiceProvider
from app.viewer.domain.viewer_session_service import ViewerTimeService


class HandleChatMessageUseCase:

    def __init__(
        self,
        chat_use_case_provider: ChatUseCaseProvider,
        economy_service_provider: EconomyServiceProvider,
        stream_service_provider: StreamServiceProvider,
        viewer_service_factory: Callable[[Session], ViewerTimeService],
        intent_use_case: IntentUseCase,
        prompt_service: PromptService,
        generate_response_fn: Callable[[str, str], str],
    ):
        self._chat_use_case_provider = chat_use_case_provider
        self._economy_service_provider = economy_service_provider
        self._stream_service_provider = stream_service_provider
        self._viewer_service_factory = viewer_service_factory
        self._intent_use_case = intent_use_case
        self._prompt_service = prompt_service
        self._generate_response_fn = generate_response_fn

    async def handle(
        self,
        db_session_provider: Callable[[], ContextManager],
        dto: ChatMessageDTO,
    ) -> Optional[str]:

        with db_session_provider() as db:
            self._chat_use_case_provider.get(db).save_chat_message(
                channel_name=dto.channel_name,
                user_name=dto.user_name,
                content=dto.message,
                current_time=dto.occurred_at
            )
            self._economy_service_provider.get(db).process_user_message_activity(
                channel_name=dto.channel_name,
                user_name=dto.user_name,
            )
            active_stream = self._stream_service_provider.get(db).get_active_stream(dto.channel_name)
            if active_stream:
                self._viewer_service_factory(db).update_viewer_session(
                    stream_id=active_stream.id,
                    channel_name=dto.channel_name,
                    user_name=dto.user_name,
                    current_time=dto.occurred_at,
                )

        intent = self._intent_use_case.get_intent_from_text(dto.message)

        prompt = None
        if intent == Intent.JACKBOX:
            prompt = self._prompt_service.get_jackbox_prompt(dto.display_name, dto.message)
        elif intent == Intent.DANKAR_CUT:
            prompt = self._prompt_service.get_dankar_cut_prompt(dto.display_name, dto.message)
        elif intent == Intent.HELLO:
            prompt = self._prompt_service.get_hello_prompt(dto.display_name, dto.message)

        if prompt is None:
            return None

        result = self._generate_response_fn(prompt, dto.channel_name)

        with db_session_provider() as db:
            self._chat_use_case_provider.get(db).save_chat_message(
                channel_name=dto.channel_name,
                user_name=dto.bot_nick.lower(),
                content=result,
                current_time=dto.occurred_at,
            )

        return result
