from app.follow.application.usecase.get_active_followers_use_case import GetActiveFollowersUseCase
from app.follow.application.usecase.get_unfollowed_use_case import GetUnfollowedUseCase
from app.follow.domain.repo import FollowersRepository


def provide_get_active_followers_use_case(followers_repository: FollowersRepository) -> GetActiveFollowersUseCase:
    return GetActiveFollowersUseCase(followers_repository)


def provide_get_unfollowed_use_case(followers_repository: FollowersRepository) -> GetUnfollowedUseCase:
    return GetUnfollowedUseCase(followers_repository)
