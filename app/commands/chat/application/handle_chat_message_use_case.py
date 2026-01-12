from app.ai.gen.application.chat_response_use_case import ChatResponseUseCase
from app.ai.gen.prompt.prompt_service import PromptService
from app.ai.intent.application.get_intent_use_case import GetIntentFromTextUseCase
from app.ai.intent.domain.models import Intent
from app.chat.domain.models import ChatMessage
from app.commands.chat.application.chat_message_uow import ChatMessageUnitOfWorkFactory
from app.commands.chat.application.model import ChatMessageDTO


class HandleChatMessageUseCase:
    def __init__(
        self,
        unit_of_work_factory: ChatMessageUnitOfWorkFactory,
        get_intent_from_text_use_case: GetIntentFromTextUseCase,
        prompt_service: PromptService,
        system_prompt: str,
        chat_response_use_case: ChatResponseUseCase,
    ):
        self._unit_of_work_factory = unit_of_work_factory
        self._get_intent_from_text_use_case = get_intent_from_text_use_case
        self._prompt_service = prompt_service
        self._system_prompt = system_prompt
        self._chat_response_use_case = chat_response_use_case

    async def handle(self, dto: ChatMessageDTO) -> str | None:
        intent = await self._get_intent_from_text_use_case.get_intent_from_text(dto.message)

        with self._unit_of_work_factory.create() as uow:
            uow.chat_repo.save(
                ChatMessage(
                    channel_name=dto.channel_name,
                    user_name=dto.user_name,
                    content=dto.message,
                    created_at=dto.occurred_at,
                )
            )
            uow.economy.process_user_message_activity(
                channel_name=dto.channel_name,
                user_name=dto.user_name,
            )
            active_stream = uow.stream_repo.get_active_stream(dto.channel_name)
            if active_stream:
                existing_session = uow.viewer_repo.get_viewer_session(
                    stream_id=active_stream.id,
                    channel_name=dto.channel_name,
                    user_name=dto.user_name,
                )
                if existing_session:
                    uow.viewer_repo.update_last_activity(
                        stream_id=active_stream.id,
                        channel_name=dto.channel_name,
                        user_name=dto.user_name,
                        current_time=dto.occurred_at,
                    )
                else:
                    uow.viewer_repo.create_view_session(
                        stream_id=active_stream.id,
                        channel_name=dto.channel_name,
                        user_name=dto.user_name,
                        current_time=dto.occurred_at,
                    )

        prompt = None
        if intent == Intent.JACKBOX:
            prompt = self._prompt_service.get_jackbox_prompt(dto.display_name, dto.message)
        elif intent == Intent.DANKAR_CUT:
            prompt = self._prompt_service.get_dankar_cut_prompt(dto.display_name, dto.message)
        elif intent == Intent.HELLO:
            prompt = self._prompt_service.get_hello_prompt(dto.display_name, dto.message)

        if prompt is None:
            return None

        with self._unit_of_work_factory.create(read_only=True) as uow_ro:
            history = uow_ro.conversation_service.get_last_messages(
                channel_name=dto.channel_name,
                system_prompt=self._system_prompt,
            )

        result = await self._chat_response_use_case.generate_response_from_history(history, prompt)

        with self._unit_of_work_factory.create() as uow:
            uow.conversation_service.save_conversation_to_db(
                channel_name=dto.channel_name,
                user_message=prompt,
                ai_message=result,
            )
            uow.chat_repo.save(
                ChatMessage(
                    channel_name=dto.channel_name,
                    user_name=dto.bot_nick.lower(),
                    content=result,
                    created_at=dto.occurred_at,
                )
            )

        return result
