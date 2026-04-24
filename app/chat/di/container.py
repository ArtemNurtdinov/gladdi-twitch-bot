from sqlalchemy.orm import Session

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.ai.gen.llm.application.usecase.generate_response_use_case import GenerateResponseUseCase
from app.ai.gen.prompt.domain.system_prompt_repository import SystemPromptRepository
from app.chat.application.job.chat_summarizer_job import ChatSummarizerJob
from app.chat.application.model.chat_summary_state import ChatSummaryState
from app.chat.application.uow.chat_summarizer_uow import ChatSummarizerUnitOfWorkFactory
from app.chat.application.uow.chat_use_case_uow import ChatUseCaseUnitOfWorkFactory
from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.chat.application.usecase.handle_chat_summarizer_use_case import HandleChatSummarizerUseCase
from app.chat.domain.repo import ChatRepository
from app.chat.infrastructure.chat_repository import ChatRepositoryImpl
from app.chat.infrastructure.uow.chat_summarizer_uow import SqlAlchemyChatSummarizerUnitOfWorkFactory
from app.chat.infrastructure.uow.chat_use_case_uow import SqlAlchemyChatUseCaseUnitOfWorkFactory
from app.core.common.session.session_scoped_factory import SessionScopedFactory
from app.core.logger.domain.logger import Logger
from app.economy.domain.economy_policy import EconomyPolicy
from app.platform.chat.application.uow.chat_message_uow import ChatMessageUnitOfWorkFactory
from app.platform.chat.infrastructure.chat_message_uow import SqlAlchemyChatMessageUnitOfWorkFactory
from app.stream.domain.repo import StreamRepository
from app.viewer.session.domain.repository import ViewerRepository
from core.types import SessionFactory


class ChatContainer:
    def __init__(self, session_factory_rw: SessionFactory, session_factory_ro: SessionFactory, logger: Logger):
        self._session_factory_rw = session_factory_rw
        self._session_factory_ro = session_factory_ro
        self.chat_repository_factory = SessionScopedFactory(self.chat_repository)
        self._logger = logger.create_child(__name__)

    def chat_repository(self, session: Session) -> ChatRepository:
        return ChatRepositoryImpl(session)

    def chat_use_case_uow_factory(self) -> ChatUseCaseUnitOfWorkFactory:
        return SqlAlchemyChatUseCaseUnitOfWorkFactory(
            session_factory_rw=self._session_factory_rw,
            session_factory_ro=self._session_factory_ro,
            chat_repository_factory=self.chat_repository_factory,
        )

    def chat_use_case(self) -> ChatUseCase:
        chat_use_case_uow_factory = self.chat_use_case_uow_factory()
        return ChatUseCase(chat_use_case_uow_factory)

    def chat_summarizer_uow_factory(
        self, stream_repository_factory: SessionScopedFactory[StreamRepository]
    ) -> ChatSummarizerUnitOfWorkFactory:
        chat_use_case = self.chat_use_case()
        return SqlAlchemyChatSummarizerUnitOfWorkFactory(
            session_factory_ro=self._session_factory_ro,
            session_factory_rw=self._session_factory_rw,
            stream_repository_factory=stream_repository_factory,
            chat_use_case=chat_use_case,
        )

    def handle_chat_summarizer_use_case(
        self,
        stream_repository_factory: SessionScopedFactory[StreamRepository],
        generate_response_use_case_factory: SessionScopedFactory[GenerateResponseUseCase],
    ) -> HandleChatSummarizerUseCase:
        chat_summarizer_uow_factory = self.chat_summarizer_uow_factory(stream_repository_factory)
        return HandleChatSummarizerUseCase(chat_summarizer_uow_factory, generate_response_use_case_factory, self._session_factory_ro)

    def chat_summarizer_job(
        self,
        stream_repository_factory: SessionScopedFactory[StreamRepository],
        generate_response_use_case_factory: SessionScopedFactory[GenerateResponseUseCase],
        chat_summary_state: ChatSummaryState,
    ) -> ChatSummarizerJob:
        handle_chat_summarizer_use_case = self.handle_chat_summarizer_use_case(
            stream_repository_factory, generate_response_use_case_factory
        )
        return ChatSummarizerJob(handle_chat_summarizer_use_case, chat_summary_state, self._logger)

    def chat_message_uow_factory(
        self,
        economy_policy_factory: SessionScopedFactory[EconomyPolicy],
        stream_repository_factory: SessionScopedFactory[StreamRepository],
        viewer_repository_factory: SessionScopedFactory[ViewerRepository],
        conversation_service_factory: SessionScopedFactory[ConversationService],
        system_prompt_repository_factory: SessionScopedFactory[SystemPromptRepository],
    ) -> ChatMessageUnitOfWorkFactory:
        return SqlAlchemyChatMessageUnitOfWorkFactory(
            session_factory_rw=self._session_factory_rw,
            session_factory_ro=self._session_factory_ro,
            chat_repository_factory=self.chat_repository_factory,
            economy_policy_factory=economy_policy_factory,
            stream_repository_factory=stream_repository_factory,
            viewer_repository_factory=viewer_repository_factory,
            conversation_service_factory=conversation_service_factory,
            system_prompt_repository_factory=system_prompt_repository_factory,
        )
