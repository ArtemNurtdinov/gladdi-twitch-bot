from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.orm import Session

from app.commands.follow.application.followage_port import FollowagePort
from app.commands.follow.infrastructure.followage_adapter import FollowageAdapter
from app.follow.application.followers_port import FollowersPort
from app.follow.application.followers_query_use_cases import (
    ListActiveFollowersUseCase,
    ListUnfollowedFollowersUseCase,
)
from app.follow.domain.repo import FollowersRepository
from app.follow.infrastructure.followers_adapter import FollowersAdapter
from app.follow.infrastructure.followers_repository import FollowersRepositoryImpl
from app.platform.streaming import StreamingPlatformPort
from core.db import get_db_ro
from core.provider import Provider


@dataclass
class FollowProviders:
    followage_port: FollowagePort
    followers_port: FollowersPort
    followers_repository_provider: Provider[FollowersRepository]


def build_follow_providers(platform: StreamingPlatformPort) -> FollowProviders:
    followage_port = FollowageAdapter(platform)
    followers_port = FollowersAdapter(platform)

    def followers_repository(db):
        return FollowersRepositoryImpl(db)

    return FollowProviders(
        followage_port=followage_port,
        followers_port=followers_port,
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
