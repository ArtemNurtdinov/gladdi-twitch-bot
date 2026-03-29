from fastapi import Depends
from sqlalchemy.orm import Session

from app.chat.infrastructure.adapter.stream_chat_stats_adapter import StreamChatStatsAdapter
from app.chat.infrastructure.chat_repository import ChatRepositoryImpl
from app.stream.application.port.stream_chat_stats_port import StreamChatStatsPort
from app.stream.application.usecase.stream_query_use_case import StreamQueryUseCase
from app.stream.domain.repo import StreamRepository
from app.stream.infrastructure.stream_repository import StreamRepositoryImpl
from core.db import get_db_ro


def get_stream_repo_ro(db: Session = Depends(get_db_ro)) -> StreamRepository:
    return StreamRepositoryImpl(db)


def get_stream_chat_stats_ro(db: Session = Depends(get_db_ro)) -> StreamChatStatsPort:
    return StreamChatStatsAdapter(ChatRepositoryImpl(db))


def get_stream_query_use_case_ro(
    repo: StreamRepositoryImpl = Depends(get_stream_repo_ro),
    chat_stats: StreamChatStatsPort = Depends(get_stream_chat_stats_ro),
) -> StreamQueryUseCase:
    return StreamQueryUseCase(repo, chat_stats)
