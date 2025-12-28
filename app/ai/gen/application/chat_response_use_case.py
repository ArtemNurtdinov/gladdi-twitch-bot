from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.ai.gen.domain.llm_client import LLMClient
from app.ai.gen.domain.models import AIMessage, Role
from app.ai.gen.domain.conversation_service_provider import ConversationServiceProvider


class ChatResponseUseCase:

    def __init__(
        self,
        conversation_service_provider: ConversationServiceProvider,
        llm_client: LLMClient,
        system_prompt: str,
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
    ):
        self._conversation_service_provider = conversation_service_provider
        self._llm_client = llm_client
        self._system_prompt = system_prompt
        self._db_readonly_session_provider = db_readonly_session_provider

    async def generate_response(self, prompt: str, channel_name: str) -> str:
        messages = []
        with self._db_readonly_session_provider() as db:
            history = self._conversation_service_provider.get(db).get_last_messages(
                channel_name=channel_name,
                system_prompt=self._system_prompt
            )
        messages.extend(history)
        messages.append(AIMessage(Role.USER, prompt))
        assistant_message = await self._llm_client.generate_ai_response(messages)
        return assistant_message

    async def generate_response_from_history(self, history: list[AIMessage], prompt: str) -> str:
        messages = list(history)
        messages.append(AIMessage(Role.USER, prompt))
        return await self._llm_client.generate_ai_response(messages)

    