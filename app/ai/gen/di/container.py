from sqlalchemy.orm import Session

from app.ai.gen.application.uow.chat_response_uow import ChatResponseUnitOfWorkFactory
from app.ai.gen.conversation.domain.conversation_repository import ConversationRepository
from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.ai.gen.conversation.infrastructure.conversation_repository import ConversationRepositoryImpl
from app.ai.gen.infrastructure.chat_response_uow import SqlAlchemyChatResponseUnitOfWorkFactory
from app.ai.gen.llm.infrastructure.llm_repository import LLMRepositoryImpl
from app.ai.gen.prompt.domain.system_prompt_repository import SystemPromptRepository
from app.ai.gen.prompt.infrastructure.system_prompt_repository import SystemPromptRepositoryImpl
from app.ai.gen.prompt.prompt_service import PromptService
from app.ai.intent.application.usecases.get_intent_use_case import GetIntentFromTextUseCase
from app.ai.intent.data.intent_detector_client import IntentDetectorClientImpl
from app.ai.intent.infrastructure.intent_uow import SimpleIntentUnitOfWorkFactory
from core.db import db_ro_session, db_rw_session
from core.provider import Provider


class AIContainer:
    def __init__(self, llmbox_host: str, intent_detector_host: str):
        self.llm_repository = LLMRepositoryImpl(llmbox_host)
        self.intent_detector = IntentDetectorClientImpl(intent_detector_host)
        self.prompt_service = PromptService()
        self.system_prompt_repo_provider = Provider(self._system_prompt_repository)
        self.conversation_service_provider = Provider(self._conversation_service)

    def _system_prompt_repository(self, session: Session) -> SystemPromptRepository:
        return SystemPromptRepositoryImpl(session)

    def _conversation_repository(self, session: Session) -> ConversationRepository:
        return ConversationRepositoryImpl(session)

    def _conversation_service(self, session: Session) -> ConversationService:
        conversation_repository = self._conversation_repository(session)
        return ConversationService(conversation_repository)

    def get_intent_from_text_use_case(self) -> GetIntentFromTextUseCase:
        intent_uow_factory = SimpleIntentUnitOfWorkFactory(self.intent_detector, self.llm_repository)
        return GetIntentFromTextUseCase(intent_uow_factory)

    def chat_response_uow_factory(self) -> ChatResponseUnitOfWorkFactory:
        return SqlAlchemyChatResponseUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            conversation_service_provider=self.conversation_service_provider,
        )
