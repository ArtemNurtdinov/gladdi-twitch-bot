from sqlalchemy.orm import Session

from app.ai.gen.conversation.domain.conversation_repository import ConversationRepository
from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.ai.gen.conversation.infrastructure.conversation_repository import ConversationRepositoryImpl
from app.ai.gen.llm.application.uow.chat_response_uow import ChatResponseUnitOfWorkFactory
from app.ai.gen.llm.application.usecase.generate_response_use_case import GenerateResponseUseCase
from app.ai.gen.llm.application.usecase.get_assistant_use_case import GetAssistantUseCase
from app.ai.gen.llm.application.usecase.save_assistant_use_case import SaveAssistantUseCase
from app.ai.gen.llm.domain.llm_repository import LLMRepository
from app.ai.gen.llm.infrastructure.llm_repository import LLMRepositoryImpl
from app.ai.gen.llm.infrastructure.uow.chat_response_uow import SqlAlchemyChatResponseUnitOfWorkFactory
from app.ai.gen.prompt.domain.system_prompt_repository import SystemPromptRepository
from app.ai.gen.prompt.infrastructure.system_prompt_repository import SystemPromptRepositoryImpl
from app.ai.gen.prompt.prompt_service import PromptService
from app.ai.intent.application.usecases.get_intent_use_case import GetIntentFromTextUseCase
from app.ai.intent.data.intent_detector_client import IntentDetectorClientImpl
from app.ai.intent.infrastructure.intent_uow import SimpleIntentUnitOfWorkFactory
from app.core.common.session.session_scoped_factory import SessionScopedFactory
from core.db import db_ro_session, db_rw_session
from core.provider import Provider
from core.types import SessionFactory


class AIContainer:
    def __init__(self, session_factory_rw: SessionFactory, session_factory_ro: SessionFactory, llmbox_host: str, intent_detector_host: str):
        self._session_factory_rw = session_factory_rw
        self._session_factory_ro = session_factory_ro
        self._llmbox_host = llmbox_host
        self.intent_detector = IntentDetectorClientImpl(intent_detector_host)
        self.prompt_service = PromptService()
        self.system_prompt_repository_factory = SessionScopedFactory(self._system_prompt_repository)
        self.conversation_service_factory = SessionScopedFactory(self._conversation_service)
        self.llm_repository_factory = SessionScopedFactory(self._llm_repository)
        self.generate_response_use_case_factory = SessionScopedFactory(self._generate_response_use_case)
        self.get_assistant_use_case_provider = Provider(self._get_assistant_use_case)
        self.save_assistant_use_case_provider = Provider(self._save_assistant_use_case)

    def _llm_repository(self, session: Session) -> LLMRepository:
        return LLMRepositoryImpl(self._llmbox_host, session)

    def _system_prompt_repository(self, session: Session) -> SystemPromptRepository:
        return SystemPromptRepositoryImpl(session)

    def _conversation_repository(self, session: Session) -> ConversationRepository:
        return ConversationRepositoryImpl(session)

    def _conversation_service(self, session: Session) -> ConversationService:
        conversation_repository = self._conversation_repository(session)
        return ConversationService(conversation_repository)

    def get_intent_from_text_use_case_provider(self) -> Provider[GetIntentFromTextUseCase]:
        return Provider(self._get_intent_from_text_use_case)

    def _get_intent_from_text_use_case(self, session: Session) -> GetIntentFromTextUseCase:
        llm_repository = self._llm_repository(session)
        intent_uow_factory = SimpleIntentUnitOfWorkFactory(self.intent_detector, llm_repository)
        return GetIntentFromTextUseCase(intent_uow_factory)

    def chat_response_uow_factory(self) -> ChatResponseUnitOfWorkFactory:
        return SqlAlchemyChatResponseUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            conversation_service_factory=self.conversation_service_factory,
        )

    def _generate_response_use_case(self, session: Session) -> GenerateResponseUseCase:
        llm_repository = self._llm_repository(session)
        chat_response_uow_factory = self.chat_response_uow_factory()
        return GenerateResponseUseCase(
            chat_response_uow_factory, llm_repository, self.system_prompt_repository_factory, self._session_factory_ro
        )

    def _get_assistant_use_case(self, session: Session) -> GetAssistantUseCase:
        llm_repository = self._llm_repository(session)
        return GetAssistantUseCase(llm_repository)

    def _save_assistant_use_case(self, session: Session) -> SaveAssistantUseCase:
        llm_repository = self._llm_repository(session)
        return SaveAssistantUseCase(llm_repository)
