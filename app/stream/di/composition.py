from sqlalchemy.orm import Session

from app.chat.domain.repo import ChatRepository
from app.chat.infrastructure.chat_repository import ChatRepositoryImpl
from app.stream.application.usecase.stream_query_use_case import StreamQueryUseCase
from app.stream.infrastructure.stream_repository import StreamRepositoryImpl


def get_stream_query_use_case(session: Session) -> StreamQueryUseCase:
    stream_repository = StreamRepositoryImpl(session)
    chat_repository: ChatRepository = ChatRepositoryImpl(session)
    return StreamQueryUseCase(stream_repository, chat_repository)
