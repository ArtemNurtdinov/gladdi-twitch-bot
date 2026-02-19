from fastapi import Depends
from sqlalchemy.orm import Session

from app.chat.infrastructure.chat_repository import ChatRepositoryImpl
from app.chat.infrastructure.stream_chat_stats_adapter import StreamChatStatsAdapter
from app.stream.application.stream_chat_stats_port import StreamChatStatsPort
from app.stream.application.stream_query_use_case import StreamQueryUseCase
from app.stream.domain.repo import StreamRepository
from app.stream.domain.stream_service import StreamService
from app.stream.infrastructure.stream_repository import StreamRepositoryImpl
from core.db import get_db_ro, get_db_rw


def get_stream_repo_ro(db: Session = Depends(get_db_ro)) -> StreamRepository:
    return StreamRepositoryImpl(db)


def get_stream_repo_rw(db: Session = Depends(get_db_rw)) -> StreamRepository:
    return StreamRepositoryImpl(db)


def get_stream_service_ro(repo: StreamRepositoryImpl = Depends(get_stream_repo_ro)) -> StreamService:
    return StreamService(repo)


def get_stream_service_rw(repo: StreamRepositoryImpl = Depends(get_stream_repo_rw)) -> StreamService:
    return StreamService(repo)


def get_stream_chat_stats_ro(db: Session = Depends(get_db_ro)) -> StreamChatStatsPort:
    return StreamChatStatsAdapter(ChatRepositoryImpl(db))


def get_stream_query_use_case_ro(
    repo: StreamRepositoryImpl = Depends(get_stream_repo_ro),
    chat_stats: StreamChatStatsPort = Depends(get_stream_chat_stats_ro),
) -> StreamQueryUseCase:
    return StreamQueryUseCase(repo, chat_stats)
