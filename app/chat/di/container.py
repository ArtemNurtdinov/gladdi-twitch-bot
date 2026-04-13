from sqlalchemy.orm import Session

from app.chat.application.uow.chat_summarizer_uow import ChatSummarizerUnitOfWorkFactory
from app.chat.application.uow.chat_use_case_uow import ChatUseCaseUnitOfWorkFactory
from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.chat.domain.repo import ChatRepository
from app.chat.infrastructure.chat_repository import ChatRepositoryImpl
from app.chat.infrastructure.uow.chat_summarizer_uow import SqlAlchemyChatSummarizerUnitOfWorkFactory
from app.chat.infrastructure.uow.chat_use_case_uow import SqlAlchemyChatUseCaseUnitOfWorkFactory
from app.stream.domain.repo import StreamRepository
from core.provider import Provider
from core.types import SessionFactory


class ChatContainer:
    def __init__(self, session_factory_rw: SessionFactory, session_factory_ro: SessionFactory):
        self._session_factory_rw = session_factory_rw
        self._session_factory_ro = session_factory_ro
        self.chat_repository_provider = Provider(self.chat_repository)

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
