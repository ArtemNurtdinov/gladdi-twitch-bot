from app.ai.gen.conversation.domain.models import AIMessage, Role
from app.ai.gen.llm.application.uow.chat_response_uow import ChatResponseUnitOfWorkFactory
from app.ai.gen.llm.domain.llm_repository import LLMRepository
from app.ai.gen.llm.domain.model.assistant import AIAssistant


class GenerateResponseUseCase:
    def __init__(self, chat_response_uow_factory: ChatResponseUnitOfWorkFactory, llm_repository: LLMRepository):
        self._chat_response_uow_factory = chat_response_uow_factory
        self._llm_repository = llm_repository

    async def generate_response(self, prompt: str, channel_name: str) -> str:
        with self._chat_response_uow_factory.create(read_only=True) as uow:
            system_prompt = uow.system_prompt_repository.get_system_prompt(channel_name)
            history = uow.conversation_service.get_last_messages(channel_name=channel_name, system_prompt=system_prompt.prompt)
        history.append(AIMessage(role=Role.USER, content=prompt))
        assistant = await self._llm_repository.get_assistant(channel_name)
        if assistant is None:
            assistant = AIAssistant.GPT_OSS_120B
        assistant_response = await self._llm_repository.generate_ai_response(assistant, history)
        return assistant_response.message
