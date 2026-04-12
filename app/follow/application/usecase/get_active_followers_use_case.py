from app.follow.domain.models import ChannelFollower
from app.follow.domain.repo import FollowersRepository


class GetActiveFollowersUseCase:
    def __init__(self, followers_repository: FollowersRepository):
        self.followers_repository = followers_repository

    def handle(self, channel_name: str) -> list[ChannelFollower]:
        return self.followers_repository.list_active(channel_name)
