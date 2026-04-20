from app.ai.gen.llm.application.usecase.generate_response_use_case import GenerateResponseUseCase
from app.ai.gen.prompt.prompt_service import PromptService
from app.ai.intent.application.usecases.get_intent_use_case import GetIntentFromTextUseCase
from app.ai.intent.domain.models import Intent
from app.chat.domain.model.chat_message import ChatMessage
from app.platform.chat.application.model.message import ChatMessageDTO
from app.platform.chat.application.uow.chat_message_uow import ChatMessageUnitOfWorkFactory
from core.provider import Provider
from core.types import SessionFactory


class HandleChatMessageUseCase:
    def __init__(
        self,
        chat_message_uow: ChatMessageUnitOfWorkFactory,
        get_intent_from_text_use_case: Provider[GetIntentFromTextUseCase],
        prompt_service: PromptService,
        generate_response_use_case: Provider[GenerateResponseUseCase],
        db_ro_session: SessionFactory,
    ):
        self._chat_message_uow = chat_message_uow
        self._get_intent_from_text_use_case = get_intent_from_text_use_case
        self._prompt_service = prompt_service
        self._generate_response_use_case = generate_response_use_case
        self._db_ro_session = db_ro_session

    async def handle(self, chat_message: ChatMessageDTO) -> str | None:
        with self._db_ro_session() as session:
            intent = await self._get_intent_from_text_use_case.get(session).get_intent_from_text(
                chat_message.channel_name, chat_message.message
            )

        with self._chat_message_uow.create() as uow:
            uow.chat_repo.save(
                ChatMessage(
                    channel_name=chat_message.channel_name,
                    user_name=chat_message.user_name,
                    content=chat_message.message,
                    created_at=chat_message.occurred_at,
                )
            )
            uow.economy.process_user_message_activity(
                channel_name=chat_message.channel_name,
                user_name=chat_message.user_name,
            )
            active_stream = uow.stream_repo.get_active_stream(chat_message.channel_name)
            if active_stream:
                existing_session = uow.viewer_repo.get_viewer_session(
                    stream_id=active_stream.id,
                    channel_name=chat_message.channel_name,
                    user_name=chat_message.user_name,
                )
                if existing_session:
                    uow.viewer_repo.update_last_activity(
                        stream_id=active_stream.id,
                        channel_name=chat_message.channel_name,
                        user_name=chat_message.user_name,
                        current_time=chat_message.occurred_at,
                    )
                else:
                    uow.viewer_repo.create_view_session(
                        stream_id=active_stream.id,
                        channel_name=chat_message.channel_name,
                        user_name=chat_message.user_name,
                        current_time=chat_message.occurred_at,
                    )

        prompt = None
        if intent == Intent.JACKBOX:
            prompt = self._prompt_service.get_jackbox_prompt(chat_message.display_name, chat_message.message)
        elif intent == Intent.DANKAR_CUT:
            prompt = self._prompt_service.get_dankar_cut_prompt(chat_message.display_name, chat_message.message)
        elif intent == Intent.HELLO:
            prompt = self._prompt_service.get_hello_prompt(chat_message.display_name, chat_message.message)

        if prompt is None:
            return None

        with self._db_ro_session() as session:
            result = await self._generate_response_use_case.get(session).generate_response(prompt, chat_message.channel_name)

        with self._chat_message_uow.create() as uow:
            uow.conversation_service.save_conversation_to_db(
                channel_name=chat_message.channel_name,
                user_message=prompt,
                ai_message=result,
            )
            uow.chat_repo.save(
                ChatMessage(
                    channel_name=chat_message.channel_name,
                    user_name=chat_message.user_name,
                    content=chat_message.message,
                    created_at=chat_message.occurred_at,
                )
            )
            uow.chat_repo.save(
                ChatMessage(
                    channel_name=chat_message.channel_name,
                    user_name=chat_message.bot_name.lower(),
                    content=result,
                    created_at=chat_message.occurred_at,
                )
            )

        return result
