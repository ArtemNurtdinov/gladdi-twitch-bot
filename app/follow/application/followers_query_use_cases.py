from __future__ import annotations

from datetime import datetime

from app.follow.application.model import FollowerDetailResult
from app.follow.application.user_balance_port import UserBalanceQueryPort
from app.follow.application.user_sessions_port import UserSessionsQueryPort
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


class GetFollowerDetailUseCase:
    def __init__(
        self,
        repo: FollowersRepository,
        balance_port: UserBalanceQueryPort,
        sessions_port: UserSessionsQueryPort,
    ):
        self._repo = repo
        self._balance_port = balance_port
        self._sessions_port = sessions_port

    def handle(self, channel_name: str, user_name: str) -> FollowerDetailResult:
        follower = self._repo.get_by_user_name(channel_name, user_name)
        if not follower:
            follower = ChannelFollower(
                id=0,
                channel_name=channel_name,
                user_id="",
                user_name=user_name,
                display_name=user_name,
                followed_at=None,
                first_seen_at=None,
                last_seen_at=None,
                unfollowed_at=None,
                is_active=False,
                created_at=None,
                updated_at=None,
            )
        balance = self._balance_port.get_balance(channel_name, user_name)
        sessions = self._sessions_port.get_user_sessions(channel_name, user_name)
        return FollowerDetailResult(follower=follower, balance=balance, sessions=sessions)
