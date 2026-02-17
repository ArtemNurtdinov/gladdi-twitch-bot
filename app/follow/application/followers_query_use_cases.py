from __future__ import annotations

from datetime import datetime

from app.follow.domain.models import ChannelFollower
from app.follow.domain.repo import FollowersRepository


class ListActiveFollowersUseCase:
    def __init__(self, repo: FollowersRepository):
        self._repo = repo

    def handle(self, channel_name: str) -> list[ChannelFollower]:
        return self._repo.list_active(channel_name)


class ListUnfollowedFollowersUseCase:
    def __init__(self, repo: FollowersRepository):
        self._repo = repo

    def handle(
        self,
        channel_name: str,
        since: datetime,
        until: datetime | None = None,
    ) -> list[ChannelFollower]:
        return self._repo.list_unfollowed_since(channel_name, since, until)
