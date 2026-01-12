from collections.abc import Callable
from contextlib import AbstractContextManager

from sqlalchemy.orm import Session

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.ai.gen.conversation.domain.models import AIMessage, Role
from app.ai.gen.llm.domain.llm_client_port import LLMClientPort
from core.provider import Provider


class ChatResponseUseCase:
    def __init__(
        self,
        conversation_service_provider: Provider[ConversationService],
        llm_client: LLMClientPort,
        system_prompt: str,
        db_readonly_session_provider: Callable[[], AbstractContextManager[Session]],
    ):
        self._conversation_service_provider = conversation_service_provider
        self._llm_client = llm_client
        self._system_prompt = system_prompt
        self._db_readonly_session_provider = db_readonly_session_provider

    async def generate_response(self, prompt: str, channel_name: str) -> str:
        with self._db_readonly_session_provider() as db:
            history = self._conversation_service_provider.get(db).get_last_messages(
                channel_name=channel_name, system_prompt=self._system_prompt
            )
        history.append(AIMessage(role=Role.USER, content=prompt))
        assistant_response = await self._llm_client.generate_ai_response(history)
        return assistant_response.message

    async def generate_response_from_history(self, history: list[AIMessage], prompt: str) -> str:
        messages = list(history)
        messages.append(AIMessage(role=Role.USER, content=prompt))
        assistant_response = await self._llm_client.generate_ai_response(messages)
        return assistant_response.message
