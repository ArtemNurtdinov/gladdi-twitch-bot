from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.ai.application.conversation_service import ConversationService
from app.ai.application.intent_use_case import IntentUseCase
from app.ai.application.prompt_service import PromptService
from app.ai.domain.models import Intent
from app.chat.application.chat_use_case import ChatUseCase
from app.twitch.application.interaction.ask.dto import AskCommandDTO
from app.twitch.application.shared import ChatResponder
from app.twitch.application.shared.chat_use_case_provider import ChatUseCaseProvider


class HandleAskUseCase:

    def __init__(
        self,
        intent_use_case: IntentUseCase,
        prompt_service: PromptService,
        ai_conversation_use_case_factory: Callable[[Session], ConversationService],
        chat_use_case_provider: ChatUseCaseProvider,
        chat_responder: ChatResponder,
    ):
        self._intent_use_case = intent_use_case
        self._prompt_service = prompt_service
        self._ai_conversation_use_case_factory = ai_conversation_use_case_factory
        self._chat_use_case_provider = chat_use_case_provider
        self._chat_responder = chat_responder

    async def handle(
        self,
        db_session_provider: Callable[[], ContextManager[Session]],
        dto: AskCommandDTO,
    ) -> str:

        intent = self._intent_use_case.get_intent_from_text(dto.message)

        if intent == Intent.JACKBOX:
            prompt = self._prompt_service.get_jackbox_prompt(dto.display_name, dto.message)
        elif intent == Intent.SKUF_FEMBOY:
            prompt = self._prompt_service.get_skuf_femboy_prompt(dto.display_name, dto.message)
        elif intent == Intent.DANKAR_CUT:
            prompt = self._prompt_service.get_dankar_cut_prompt(dto.display_name, dto.message)
        elif intent == Intent.HELLO:
            prompt = self._prompt_service.get_hello_prompt(dto.display_name, dto.message)
        else:
            prompt = self._prompt_service.get_default_prompt(dto.display_name, dto.message)

        result = self._chat_responder.generate_response(prompt, dto.channel_name)

        with db_session_provider() as db:
            self._ai_conversation_use_case_factory(db).save_conversation_to_db(
                channel_name=dto.channel_name,
                user_message=prompt,
                ai_message=result,
            )
            self._chat_use_case_provider.get(db).save_chat_message(
                channel_name=dto.channel_name,
                user_name=dto.bot_nick.lower(),
                content=result,
                current_time=dto.occurred_at,
            )

        return result

