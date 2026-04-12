from fastapi import Depends
from sqlalchemy.orm import Session

from app.chat.domain.repo import ChatRepository
from app.chat.infrastructure.chat_repository import ChatRepositoryImpl
from app.stream.application.usecase.stream_query_use_case import StreamQueryUseCase
from app.stream.domain.repo import StreamRepository
from app.stream.infrastructure.stream_repository import StreamRepositoryImpl
from core.db import get_db


class StreamContainer:
    def __init__(self, session: Session):
        self.stream_repository: StreamRepository = StreamRepositoryImpl(session)
        self.chat_repository: ChatRepository = ChatRepositoryImpl(session)
        self.stream_use_case = StreamQueryUseCase(self.stream_repository, self.chat_repository)


def get_stream_container(session: Session = Depends(get_db)) -> StreamContainer:
    return StreamContainer(session)
