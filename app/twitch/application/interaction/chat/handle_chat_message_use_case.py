from typing import Optional

from app.ai.application.intent_use_case import IntentUseCase
from app.ai.application.prompt_service import PromptService
from app.ai.domain.models import Intent
from app.twitch.application.interaction.chat.chat_message_uow import ChatMessageUnitOfWorkFactory, ChatMessageUnitOfWorkRoFactory
from app.twitch.application.interaction.chat.dto import ChatMessageDTO
from app.twitch.application.shared import ChatResponder


class HandleChatMessageUseCase:

    def __init__(
        self,
        unit_of_work_factory: ChatMessageUnitOfWorkFactory,
        unit_of_work_ro_factory: ChatMessageUnitOfWorkRoFactory,
        intent_use_case: IntentUseCase,
        prompt_service: PromptService,
        system_prompt: str,
        chat_responder: ChatResponder
    ):
        self._unit_of_work_factory = unit_of_work_factory
        self._unit_of_work_ro_factory = unit_of_work_ro_factory
        self._intent_use_case = intent_use_case
        self._prompt_service = prompt_service
        self._system_prompt = system_prompt
        self._chat_responder = chat_responder

    async def handle(self, dto: ChatMessageDTO) -> Optional[str]:
        intent = await self._intent_use_case.get_intent_from_text(dto.message)

        prompt = None
        if intent == Intent.JACKBOX:
            prompt = self._prompt_service.get_jackbox_prompt(dto.display_name, dto.message)
        elif intent == Intent.DANKAR_CUT:
            prompt = self._prompt_service.get_dankar_cut_prompt(dto.display_name, dto.message)
        elif intent == Intent.HELLO:
            prompt = self._prompt_service.get_hello_prompt(dto.display_name, dto.message)

        if prompt is None:
            return None

        with self._unit_of_work_factory.create() as uow:
            uow.chat.save_chat_message(
                channel_name=dto.channel_name,
                user_name=dto.user_name,
                content=dto.message,
                current_time=dto.occurred_at
            )
            uow.economy.process_user_message_activity(
                channel_name=dto.channel_name,
                user_name=dto.user_name,
            )
            active_stream = uow.stream.get_active_stream(dto.channel_name)
            if active_stream:
                uow.viewer.update_viewer_session(
                    stream_id=active_stream.id,
                    channel_name=dto.channel_name,
                    user_name=dto.user_name,
                    current_time=dto.occurred_at,
                )

        with self._unit_of_work_ro_factory.create() as uow_ro:
            history = uow_ro.conversation.get_last_messages(
                channel_name=dto.channel_name,
                system_prompt=self._system_prompt,
            )

        result = await self._chat_responder.generate_response_from_history(history, prompt)

        with self._unit_of_work_factory.create() as uow:
            uow.conversation.save_conversation_to_db(
                channel_name=dto.channel_name,
                user_message=prompt,
                ai_message=result,
            )
            uow.chat.save_chat_message(
                channel_name=dto.channel_name,
                user_name=dto.bot_nick.lower(),
                content=result,
                current_time=dto.occurred_at,
            )

        return result
