from sqlalchemy.orm import Session

from app.chat.domain.repo import ChatRepository
from app.chat.infrastructure.chat_repository import ChatRepositoryImpl
from app.core.common.session.session_scoped_factory import SessionScopedFactory
from app.stream.application.usecase.stream_query_use_case import StreamQueryUseCase
from app.stream.domain.repo import StreamRepository
from app.stream.infrastructure.stream_repository import StreamRepositoryImpl


class StreamContainer:
    def __init__(self):
        self.stream_repository_factory: SessionScopedFactory[StreamRepository] = SessionScopedFactory(self._stream_repository)
        self.stream_use_case_factory: SessionScopedFactory[StreamQueryUseCase] = SessionScopedFactory(self._stream_use_case)

    def _stream_repository(self, session: Session) -> StreamRepository:
        return StreamRepositoryImpl(session)

    def _stream_use_case(self, session: Session) -> StreamQueryUseCase:
        stream_repository = self._stream_repository(session)
        chat_repository: ChatRepository = ChatRepositoryImpl(session)
        return StreamQueryUseCase(stream_repository, chat_repository)
