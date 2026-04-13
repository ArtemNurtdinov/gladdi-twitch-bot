from sqlalchemy.orm import Session

from app.follow.application.usecase.get_active_followers_use_case import GetActiveFollowersUseCase
from app.follow.application.usecase.get_unfollowed_use_case import GetUnfollowedUseCase
from app.follow.domain.repo import FollowersRepository
from app.follow.infrastructure.followers_repository import FollowersRepositoryImpl


class FollowContainer:
    def _followers_repository(self, session: Session) -> FollowersRepository:
        return FollowersRepositoryImpl(session)

    def get_active_followers_use_case(self, session: Session) -> GetActiveFollowersUseCase:
        followers_repository = self._followers_repository(session)
        return GetActiveFollowersUseCase(followers_repository)

    def get_unfollowed_use_case(self, session: Session) -> GetUnfollowedUseCase:
        followers_repository = self._followers_repository(session)
        return GetUnfollowedUseCase(followers_repository)
