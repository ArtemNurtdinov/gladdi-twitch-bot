from app.ai.gen.conversation.domain.models import AIMessage, Role
from app.ai.gen.llm.application.uow.chat_response_uow import ChatResponseUnitOfWorkFactory
from app.ai.gen.llm.domain.llm_repository import LLMRepository


class GenerateResponseUseCase:
    def __init__(self, chat_response_uow_factory: ChatResponseUnitOfWorkFactory, llm_repository: LLMRepository):
        self._chat_response_uow_factory = chat_response_uow_factory
        self._llm_repository = llm_repository

    async def generate_response(self, prompt: str, channel_name: str, *, include_history: bool = True) -> str:
        with self._chat_response_uow_factory.create(read_only=True) as uow:
            system_prompt = uow.system_prompt_repository.get_system_prompt(channel_name)
            if include_history:
                messages = uow.conversation_service.get_last_messages(channel_name=channel_name, system_prompt=system_prompt.prompt)
            else:
                messages = [AIMessage(role=Role.SYSTEM, content=system_prompt.prompt)]
        messages.append(AIMessage(role=Role.USER, content=prompt))
        assistant_response = await self._llm_repository.generate_ai_response(messages)
        return assistant_response.message
