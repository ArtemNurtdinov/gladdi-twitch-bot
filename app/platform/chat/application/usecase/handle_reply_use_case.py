from app.ai.gen.llm.application.usecase.generate_response_use_case import GenerateResponseUseCase
from app.ai.gen.prompt.prompt_service import PromptService
from app.chat.domain.model.chat_message import ChatMessage
from app.platform.chat.application.model.message import ChatMessageDTO
from app.platform.chat.application.uow.chat_message_uow import ChatMessageUnitOfWorkFactory
from core.provider import Provider
from core.types import SessionFactory


class HandleReplyUseCase:
    def __init__(
        self,
        chat_message_uow: ChatMessageUnitOfWorkFactory,
        prompt_service: PromptService,
        generate_response_use_case: Provider[GenerateResponseUseCase],
        db_ro_session: SessionFactory,
    ):
        self._chat_message_uow = chat_message_uow
        self._prompt_service = prompt_service
        self._generate_response_use_case = generate_response_use_case
        self._db_ro_session = db_ro_session

    async def handle(self, chat_message: ChatMessageDTO) -> str:
        prompt = self._prompt_service.get_reply_prompt(chat_message.display_name, chat_message.message)
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
