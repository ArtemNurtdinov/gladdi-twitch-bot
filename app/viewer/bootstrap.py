from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.orm import Session

from app.viewer.application.usecases.get_user_sessions_use_case import GetUserSessionsUseCase
from app.viewer.domain.repo import ViewerRepository
from app.viewer.infrastructure.viewer_repository import ViewerRepositoryImpl
from core.db import get_db_ro, get_db_rw
from core.provider import Provider


@dataclass
class ViewerProviders:
    viewer_query_service_provider: Provider[GetUserSessionsUseCase]
    viewer_repo_provider: Provider[ViewerRepository]


def build_viewer_providers() -> ViewerProviders:

    def viewer_query_service(db):
        return GetUserSessionsUseCase(ViewerRepositoryImpl(db))

    def viewer_repo(db):
        return ViewerRepositoryImpl(db)

    return ViewerProviders(
        viewer_query_service_provider=Provider(viewer_query_service),
        viewer_repo_provider=Provider(viewer_repo),
    )


def get_viewer_repo_ro(db: Session = Depends(get_db_ro)) -> ViewerRepository:
    return ViewerRepositoryImpl(db)


def get_viewer_repo_rw(db: Session = Depends(get_db_rw)) -> ViewerRepository:
    return ViewerRepositoryImpl(db)


def get_viewer_service_ro(repo: ViewerRepositoryImpl = Depends(get_viewer_repo_ro)) -> GetUserSessionsUseCase:
    return GetUserSessionsUseCase(repo)
