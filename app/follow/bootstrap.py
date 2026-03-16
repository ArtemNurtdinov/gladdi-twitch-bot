from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.orm import Session

from app.follow.application.usecases.followers_query_use_cases import (
    ListActiveFollowersUseCase,
    ListUnfollowedFollowersUseCase,
)
from app.follow.domain.repo import FollowersRepository
from app.follow.infrastructure.followers_repository import FollowersRepositoryImpl
from core.db import get_db_ro
from core.provider import Provider


@dataclass
class FollowProviders:
    followers_repository_provider: Provider[FollowersRepository]


def build_follow_providers() -> FollowProviders:
    def followers_repository(db):
        return FollowersRepositoryImpl(db)

    return FollowProviders(
        followers_repository_provider=Provider(followers_repository),
    )


def get_followers_repo_ro(db: Session = Depends(get_db_ro)) -> FollowersRepositoryImpl:
    return FollowersRepositoryImpl(db)


def get_list_active_followers_use_case(
    repo: FollowersRepositoryImpl = Depends(get_followers_repo_ro),
) -> ListActiveFollowersUseCase:
    return ListActiveFollowersUseCase(repo)


def get_list_unfollowed_followers_use_case(
    repo: FollowersRepositoryImpl = Depends(get_followers_repo_ro),
) -> ListUnfollowedFollowersUseCase:
    return ListUnfollowedFollowersUseCase(repo)
