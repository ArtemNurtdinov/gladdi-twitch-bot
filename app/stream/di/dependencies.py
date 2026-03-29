from sqlalchemy.orm import Session

from app.chat.infrastructure.adapter.stream_chat_stats_adapter import StreamChatStatsAdapter
from app.chat.infrastructure.chat_repository import ChatRepositoryImpl
from app.stream.application.port.stream_chat_stats_port import StreamChatStatsPort
from app.stream.domain.repo import StreamRepository
from app.stream.infrastructure.stream_repository import StreamRepositoryImpl


def provide_stream_repository(session: Session) -> StreamRepository:
    return StreamRepositoryImpl(session)


def provide_stream_chat_stats_ro(session: Session) -> StreamChatStatsPort:
    return StreamChatStatsAdapter(ChatRepositoryImpl(session))


def provide_stream_chat_stats_port(session: Session) -> StreamChatStatsPort:
    return StreamChatStatsAdapter(ChatRepositoryImpl(session))
