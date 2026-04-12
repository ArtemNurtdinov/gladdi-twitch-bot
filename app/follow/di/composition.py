from sqlalchemy.orm import Session

from app.follow.application.usecase.get_active_followers_use_case import GetActiveFollowersUseCase
from app.follow.application.usecase.get_unfollowed_use_case import GetUnfollowedUseCase
from app.follow.domain.repo import FollowersRepository
from app.follow.infrastructure.followers_repository import FollowersRepositoryImpl


def get_active_followers_use_case(session: Session) -> GetActiveFollowersUseCase:
    followers_repository: FollowersRepository = FollowersRepositoryImpl(session)
    return GetActiveFollowersUseCase(followers_repository)


def get_unfollowed_use_case(session: Session) -> GetUnfollowedUseCase:
    followers_repository: FollowersRepository = FollowersRepositoryImpl(session)
    return GetUnfollowedUseCase(followers_repository)
