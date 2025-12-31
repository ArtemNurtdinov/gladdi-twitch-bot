from fastapi import Depends
from sqlalchemy.orm import Session

from app.viewer.data.viewer_repository import ViewerRepositoryImpl
from app.viewer.domain.repo import ViewerRepository
from app.viewer.domain.viewer_session_service import ViewerTimeService
from core.db import get_db_ro, get_db_rw


def get_viewer_repo_ro(db: Session = Depends(get_db_ro)) -> ViewerRepository:
    return ViewerRepositoryImpl(db)


def get_viewer_repo_rw(db: Session = Depends(get_db_rw)) -> ViewerRepository:
    return ViewerRepositoryImpl(db)


def get_viewer_service_ro(repo: ViewerRepositoryImpl = Depends(get_viewer_repo_ro)) -> ViewerTimeService:
    return ViewerTimeService(repo)


def get_viewer_service_rw(repo: ViewerRepositoryImpl = Depends(get_viewer_repo_rw)) -> ViewerTimeService:
    return ViewerTimeService(repo)

