from fastapi import Depends
from sqlalchemy.orm import Session

from core.db import get_db_ro
from app.follow.infrastructure.followers_repository import FollowersRepositoryImpl
from app.follow.application.followers_query_use_cases import (
    ListActiveFollowersUseCase,
    ListNewFollowersUseCase,
    ListUnfollowedFollowersUseCase,
    GetFollowerDetailUseCase,
)


def get_followers_repo_ro(db: Session = Depends(get_db_ro)) -> FollowersRepositoryImpl:
    return FollowersRepositoryImpl(db)


def get_list_active_followers_use_case(
    repo: FollowersRepositoryImpl = Depends(get_followers_repo_ro),
) -> ListActiveFollowersUseCase:
    return ListActiveFollowersUseCase(repo)


def get_list_new_followers_use_case(
    repo: FollowersRepositoryImpl = Depends(get_followers_repo_ro),
) -> ListNewFollowersUseCase:
    return ListNewFollowersUseCase(repo)


def get_list_unfollowed_followers_use_case(
    repo: FollowersRepositoryImpl = Depends(get_followers_repo_ro),
) -> ListUnfollowedFollowersUseCase:
    return ListUnfollowedFollowersUseCase(repo)


def get_follower_detail_use_case(
    repo: FollowersRepositoryImpl = Depends(get_followers_repo_ro),
) -> GetFollowerDetailUseCase:
    return GetFollowerDetailUseCase(repo)

