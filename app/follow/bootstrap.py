from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.orm import Session

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
