from app.ai.gen.application.uow.chat_response_uow import ChatResponseUnitOfWorkFactory
from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.ai.gen.infrastructure.chat_response_uow import SqlAlchemyChatResponseUnitOfWorkFactory
from app.ai.gen.llm.infrastructure.llm_repository import LLMRepositoryImpl
from app.ai.gen.prompt.infrastructure.system_prompt_repository import SystemPromptRepositoryImpl
from core.db import db_ro_session, db_rw_session
from core.provider import Provider


class AIContainer:
    def __init__(self, llmbox_host: str):
        self.llm_repository = LLMRepositoryImpl(llmbox_host)
        self.system_prompt_repo_provider = Provider(lambda session: SystemPromptRepositoryImpl(session))

    def chat_response_uow_factory(self, conversation_service_provider: Provider[ConversationService]) -> ChatResponseUnitOfWorkFactory:
        return SqlAlchemyChatResponseUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            conversation_service_provider=conversation_service_provider,
        )
