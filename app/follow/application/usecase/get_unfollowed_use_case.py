from app.follow.domain.models import ChannelFollower
from app.follow.domain.repo import FollowersRepository


class GetUnfollowedUseCase:
    def __init__(self, followers_repository: FollowersRepository) -> None:
        self._followers_repository = followers_repository

    def handle(self, channel_name: str) -> list[ChannelFollower]:
        unfollowed = self._followers_repository.list_unfollowed_since(channel_name)
        return sorted(unfollowed, key=lambda f: f.unfollowed_at, reverse=True)
