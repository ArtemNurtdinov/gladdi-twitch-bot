from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.ai.application.conversation_service import ConversationService
from app.ai.domain.models import AIMessage, Role
from app.ai.data.llm_client import LLMClientImpl


class ChatResponder:

    def __init__(
        self,
        ai_conversation_use_case_factory: Callable[[Session], ConversationService],
        llm_client: LLMClientImpl,
        system_prompt: str,
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
    ):
        self._ai_conversation_use_case_factory = ai_conversation_use_case_factory
        self._llm_client = llm_client
        self._system_prompt = system_prompt
        self._db_readonly_session_provider = db_readonly_session_provider

    def generate_response(self, prompt: str, channel_name: str) -> str:
        messages = []
        with self._db_readonly_session_provider() as db:
            history = self._ai_conversation_use_case_factory(db).get_last_messages(
                channel_name=channel_name,
                system_prompt=self._system_prompt
            )
        messages.extend(history)
        messages.append(AIMessage(Role.USER, prompt))
        assistant_message = self._llm_client.generate_ai_response(messages)
        return assistant_message

