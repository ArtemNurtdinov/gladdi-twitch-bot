from abc import ABC, abstractmethod
from datetime import datetime

from app.follow.domain.models import ChannelFollower


class FollowersRepository(ABC):
    @abstractmethod
    def list_by_channel(self, channel_name: str) -> list[ChannelFollower]: ...

    @abstractmethod
    def list_active(self, channel_name: str) -> list[ChannelFollower]: ...

    @abstractmethod
    def list_unfollowed_since(self, channel_name: str, since: datetime, until: datetime | None = None) -> list[ChannelFollower]: ...

    @abstractmethod
    def get_by_user_name(self, channel_name: str, user_name: str) -> ChannelFollower | None: ...

    @abstractmethod
    def upsert_active(
        self,
        channel_name: str,
        user_id: str,
        user_name: str,
        display_name: str,
        followed_at: datetime | None,
        seen_at: datetime,
    ): ...

    @abstractmethod
    def mark_unfollowed(self, channel_name: str, user_ids: list[str], unfollowed_at: datetime) -> None: ...
