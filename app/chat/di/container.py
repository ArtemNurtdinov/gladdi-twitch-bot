from sqlalchemy.orm import Session

from app.ai.gen.application.use_cases.generate_response_use_case import GenerateResponseUseCase
from app.ai.gen.conversation.domain.conversation_service import ConversationService
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
from app.core.logger.domain.logger import Logger
from app.economy.domain.economy_policy import EconomyPolicy
from app.platform.chat.application.chat_message_uow import ChatMessageUnitOfWorkFactory
from app.platform.chat.infrastructure.chat_message_uow import SqlAlchemyChatMessageUnitOfWorkFactory
from app.stream.domain.repo import StreamRepository
from app.viewer.session.domain.repository import ViewerRepository
from core.provider import Provider
from core.types import SessionFactory


class ChatContainer:
    def __init__(self, session_factory_rw: SessionFactory, session_factory_ro: SessionFactory, logger: Logger):
        self._session_factory_rw = session_factory_rw
        self._session_factory_ro = session_factory_ro
        self.chat_repository_provider = Provider(self.chat_repository)
        self._logger = logger.create_child(__name__)

    def chat_repository(self, session: Session) -> ChatRepository:
        return ChatRepositoryImpl(session)

    def chat_use_case_uow_factory(self) -> ChatUseCaseUnitOfWorkFactory:
        return SqlAlchemyChatUseCaseUnitOfWorkFactory(
            session_factory_rw=self._session_factory_rw,
            session_factory_ro=self._session_factory_ro,
            chat_repo_provider=self.chat_repository_provider,
        )

    def chat_use_case(self) -> ChatUseCase:
        chat_use_case_uow_factory = self.chat_use_case_uow_factory()
        return ChatUseCase(chat_use_case_uow_factory)

    def chat_summarizer_uow_factory(self, stream_repository_provider: Provider[StreamRepository]) -> ChatSummarizerUnitOfWorkFactory:
        chat_use_case = self.chat_use_case()
        return SqlAlchemyChatSummarizerUnitOfWorkFactory(
            session_factory_ro=self._session_factory_ro,
            session_factory_rw=self._session_factory_rw,
            stream_repository_provider=stream_repository_provider,
            chat_use_case=chat_use_case,
        )

    def handle_chat_summarizer_use_case(
        self, stream_repository_provider: Provider[StreamRepository], generate_response_use_case: GenerateResponseUseCase
    ) -> HandleChatSummarizerUseCase:
        chat_summarizer_uow_factory = self.chat_summarizer_uow_factory(stream_repository_provider)
        return HandleChatSummarizerUseCase(chat_summarizer_uow_factory, generate_response_use_case)

    def chat_summarizer_job(
        self,
        channel_name: str,
        stream_repository_provider: Provider[StreamRepository],
        generate_response_use_case: GenerateResponseUseCase,
        chat_summary_state: ChatSummaryState,
    ) -> ChatSummarizerJob:
        handle_chat_summarizer_use_case = self.handle_chat_summarizer_use_case(stream_repository_provider, generate_response_use_case)
        return ChatSummarizerJob(channel_name, handle_chat_summarizer_use_case, chat_summary_state, self._logger)

    def chat_message_uow_factory(
        self,
        economy_policy_provider: Provider[EconomyPolicy],
        stream_repository_provider: Provider[StreamRepository],
        viewer_repository_provider: Provider[ViewerRepository],
        conversation_service_provider: Provider[ConversationService],
        system_prompt_repository_provider: Provider[SystemPromptRepository],
    ) -> ChatMessageUnitOfWorkFactory:
        return SqlAlchemyChatMessageUnitOfWorkFactory(
            session_factory_rw=self._session_factory_rw,
            session_factory_ro=self._session_factory_ro,
            chat_repo_provider=self.chat_repository_provider,
            economy_policy_provider=economy_policy_provider,
            stream_repo_provider=stream_repository_provider,
            viewer_repo_provider=viewer_repository_provider,
            conversation_service_provider=conversation_service_provider,
            system_prompt_repository_provider=system_prompt_repository_provider,
        )
