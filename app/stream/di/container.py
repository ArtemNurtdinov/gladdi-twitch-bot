from sqlalchemy.orm import Session

from app.chat.domain.repo import ChatRepository
from app.chat.infrastructure.chat_repository import ChatRepositoryImpl
from app.stream.application.usecase.stream_query_use_case import StreamQueryUseCase
from app.stream.domain.repo import StreamRepository
from app.stream.infrastructure.stream_repository import StreamRepositoryImpl
from core.provider import Provider


class StreamContainer:
    def __init__(self):
        self.stream_repository_provider: Provider[StreamRepository] = Provider(self._stream_repository)

    def _stream_repository(self, session: Session) -> StreamRepository:
        return StreamRepositoryImpl(session)

    def stream_use_case(self, session: Session) -> StreamQueryUseCase:
        stream_repository = self._stream_repository(session)
        chat_repository: ChatRepository = ChatRepositoryImpl(session)
        return StreamQueryUseCase(stream_repository, chat_repository)
