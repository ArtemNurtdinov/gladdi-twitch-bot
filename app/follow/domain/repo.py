from datetime import datetime
from typing import Protocol

from app.follow.domain.models import ChannelFollower


class FollowersRepository(Protocol):
    def list_by_channel(self, channel_name: str) -> list[ChannelFollower]: ...

    def list_active(self, channel_name: str) -> list[ChannelFollower]: ...

    def list_new_since(self, channel_name: str, since: datetime, until: datetime | None = None) -> list[ChannelFollower]: ...

    def list_unfollowed_since(self, channel_name: str, since: datetime, until: datetime | None = None) -> list[ChannelFollower]: ...

    def get_by_user_name(self, channel_name: str, user_name: str) -> ChannelFollower | None: ...

    def upsert_active(
        self,
        channel_name: str,
        user_id: str,
        user_name: str,
        display_name: str,
        followed_at: datetime | None,
        seen_at: datetime,
    ): ...

    def mark_unfollowed(self, channel_name: str, user_ids: list[str], unfollowed_at: datetime) -> None: ...
