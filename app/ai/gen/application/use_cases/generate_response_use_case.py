from app.ai.gen.application.uow.chat_response_uow import ChatResponseUnitOfWorkFactory
from app.ai.gen.conversation.domain.models import AIMessage, Role
from app.ai.gen.llm.domain.llm_repository import LLMRepository
from app.ai.gen.llm.domain.model.assistant import AIAssistant
from app.ai.gen.prompt.domain.system_prompt_repository import SystemPromptRepository
from core.provider import Provider
from core.types import SessionFactory


class GenerateResponseUseCase:
    def __init__(
        self,
        chat_response_uow_factory: ChatResponseUnitOfWorkFactory,
        llm_repository: LLMRepository,
        system_prompt_repository_provider: Provider[SystemPromptRepository],
        db_ro_session: SessionFactory,
    ):
        self._chat_response_uow_factory = chat_response_uow_factory
        self._llm_repository = llm_repository
        self._system_prompt_repository_provider = system_prompt_repository_provider
        self._db_ro_session = db_ro_session

    async def generate_response(self, prompt: str, channel_name: str) -> str:
        with self._db_ro_session() as session:
            system_prompt = self._system_prompt_repository_provider.get(session).get_system_prompt(channel_name)
        with self._chat_response_uow_factory.create(read_only=True) as uow:
            history = uow.conversation_service.get_last_messages(channel_name=channel_name, system_prompt=system_prompt.prompt)
        history.append(AIMessage(role=Role.USER, content=prompt))
        assistant_response = await self._llm_repository.generate_ai_response(history, AIAssistant.GPT_OSS_120B)
        return assistant_response.message

    async def generate_response_from_history(self, history: list[AIMessage], prompt: str) -> str:
        messages = list(history)
        messages.append(AIMessage(role=Role.USER, content=prompt))
        assistant_response = await self._llm_repository.generate_ai_response(messages, AIAssistant.GPT_OSS_120B)
        return assistant_response.message
