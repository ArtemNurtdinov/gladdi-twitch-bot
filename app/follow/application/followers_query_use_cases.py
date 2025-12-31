from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from app.follow.domain.models import ChannelFollower
from app.follow.domain.repo import FollowersRepository


class ListActiveFollowersUseCase:

    def __init__(self, repo: FollowersRepository):
        self._repo = repo

    def handle(self, channel_name: str) -> List[ChannelFollower]:
        return self._repo.list_active(channel_name)


class ListNewFollowersUseCase:

    def __init__(self, repo: FollowersRepository):
        self._repo = repo

    def handle(
        self,
        channel_name: str,
        since: datetime,
        until: Optional[datetime] = None,
    ) -> List[ChannelFollower]:
        return self._repo.list_new_since(channel_name, since, until)


class ListUnfollowedFollowersUseCase:

    def __init__(self, repo: FollowersRepository):
        self._repo = repo

    def handle(
        self,
        channel_name: str,
        since: datetime,
        until: Optional[datetime] = None,
    ) -> List[ChannelFollower]:
        return self._repo.list_unfollowed_since(channel_name, since, until)


class GetFollowerDetailUseCase:

    def __init__(self, repo: FollowersRepository):
        self._repo = repo

    def handle(self, channel_name: str, user_name: str) -> ChannelFollower | None:
        return self._repo.get_by_user_name(channel_name, user_name)

