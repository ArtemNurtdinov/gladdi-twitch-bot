from fastapi import Depends
from sqlalchemy.orm import Session

from app.stream.infrastructure.stream_repository import StreamRepositoryImpl
from app.stream.domain.repo import StreamRepository
from app.stream.domain.stream_service import StreamService
from core.db import get_db_ro, get_db_rw


def get_stream_repo_ro(db: Session = Depends(get_db_ro)) -> StreamRepository:
    return StreamRepositoryImpl(db)


def get_stream_repo_rw(db: Session = Depends(get_db_rw)) -> StreamRepository:
    return StreamRepositoryImpl(db)


def get_stream_service_ro(repo: StreamRepositoryImpl = Depends(get_stream_repo_ro)) -> StreamService:
    return StreamService(repo)


def get_stream_service_rw(repo: StreamRepositoryImpl = Depends(get_stream_repo_rw)) -> StreamService:
    return StreamService(repo)

