from sqlalchemy.orm import Session

from app.stream.application.usecase.stream_query_use_case import StreamQueryUseCase
from app.stream.di.dependencies import provide_stream_chat_stats_port
from app.stream.infrastructure.stream_repository import StreamRepositoryImpl


def get_stream_query_use_case(session: Session) -> StreamQueryUseCase:
    stream_repository = StreamRepositoryImpl(session)
    stream_chat_stats = provide_stream_chat_stats_port(session)
    return StreamQueryUseCase(stream_repository, stream_chat_stats)
