from app.ai.gen.application.use_cases.generate_response_use_case import GenerateResponseUseCase
from app.ai.gen.prompt.prompt_service import PromptService
from app.chat.domain.model.chat_message import ChatMessage
from app.platform.chat.application.chat_message_uow import ChatMessageUnitOfWorkFactory
from app.platform.chat.application.model import ChatMessageDTO


class HandleReplyUseCase:
    def __init__(
        self,
        chat_message_uow: ChatMessageUnitOfWorkFactory,
        prompt_service: PromptService,
        generate_response_use_case: GenerateResponseUseCase,
    ):
        self._chat_message_uow = chat_message_uow
        self._prompt_service = prompt_service
        self._generate_response_use_case = generate_response_use_case

    async def handle(self, chat_message: ChatMessageDTO) -> str:
        with self._chat_message_uow.create(read_only=True) as uow_ro:
            system_prompt = uow_ro.system_prompt_repository.get_system_prompt(chat_message.channel_name)
            history = uow_ro.conversation_service.get_last_messages(
                channel_name=chat_message.channel_name,
                system_prompt=system_prompt.prompt,
            )
        prompt = self._prompt_service.get_reply_prompt(chat_message.display_name, chat_message.message)
        result = await self._generate_response_use_case.generate_response_from_history(history, prompt)

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
