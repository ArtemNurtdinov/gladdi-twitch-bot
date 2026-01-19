from app.ai.gen.application.chat_response_uow import ChatResponseUnitOfWorkFactory
from app.ai.gen.conversation.domain.models import AIMessage, Role
from app.ai.gen.llm.domain.llm_client_port import LLMClientPort


class ChatResponseUseCase:
    def __init__(
        self,
        unit_of_work_factory: ChatResponseUnitOfWorkFactory,
        llm_client: LLMClientPort,
        system_prompt: str,
    ):
        self._unit_of_work_factory = unit_of_work_factory
        self._llm_client = llm_client
        self._system_prompt = system_prompt

    async def generate_response(self, prompt: str, channel_name: str) -> str:
        with self._unit_of_work_factory.create(read_only=True) as uow:
            history = uow.conversation_service.get_last_messages(channel_name=channel_name, system_prompt=self._system_prompt)
        history.append(AIMessage(role=Role.USER, content=prompt))
        assistant_response = await self._llm_client.generate_ai_response(history)
        return assistant_response.message

    async def generate_response_from_history(self, history: list[AIMessage], prompt: str) -> str:
        messages = list(history)
        messages.append(AIMessage(role=Role.USER, content=prompt))
        assistant_response = await self._llm_client.generate_ai_response(messages)
        return assistant_response.message
