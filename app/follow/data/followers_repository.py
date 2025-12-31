from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.follow.data.db.follower import ChannelFollowerRow
from app.follow.domain.models import ChannelFollower
from app.follow.domain.repo import FollowersRepository


class FollowersRepositoryImpl(FollowersRepository):

    def __init__(self, db: Session):
        self._db = db

    def _to_domain(self, row: ChannelFollowerRow) -> ChannelFollower:
        return ChannelFollower(
            id=row.id,
            channel_name=row.channel_name,
            user_id=row.user_id,
            user_name=row.user_name,
            display_name=row.display_name,
            followed_at=row.followed_at,
            first_seen_at=row.first_seen_at,
            last_seen_at=row.last_seen_at,
            unfollowed_at=row.unfollowed_at,
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def list_by_channel(self, channel_name: str) -> List[ChannelFollower]:
        rows = self._db.query(ChannelFollowerRow).filter_by(channel_name=channel_name).all()
        return [self._to_domain(row) for row in rows]

    def list_active(self, channel_name: str) -> List[ChannelFollower]:
        rows = (
            self._db.query(ChannelFollowerRow)
            .filter_by(channel_name=channel_name, is_active=True)
            .all()
        )
        return [self._to_domain(row) for row in rows]

    def list_new_since(self, channel_name: str, since: datetime, until: datetime | None = None) -> List[ChannelFollower]:
        query = (
            self._db.query(ChannelFollowerRow)
            .filter_by(channel_name=channel_name, is_active=True)
            .filter(ChannelFollowerRow.followed_at != None)
            .filter(ChannelFollowerRow.followed_at >= since)
        )
        if until:
            query = query.filter(ChannelFollowerRow.followed_at <= until)
        rows = query.all()
        return [self._to_domain(row) for row in rows]

    def list_unfollowed_since(self, channel_name: str, since: datetime, until: datetime | None = None) -> List[ChannelFollower]:
        query = (
            self._db.query(ChannelFollowerRow)
            .filter_by(channel_name=channel_name, is_active=False)
            .filter(ChannelFollowerRow.unfollowed_at != None)
            .filter(ChannelFollowerRow.unfollowed_at >= since)
        )
        if until:
            query = query.filter(ChannelFollowerRow.unfollowed_at <= until)
        rows = query.all()
        return [self._to_domain(row) for row in rows]

    def get_by_user_name(self, channel_name: str, user_name: str) -> ChannelFollower | None:
        row = (
            self._db.query(ChannelFollowerRow)
            .filter_by(channel_name=channel_name, user_name=user_name)
            .first()
        )
        return None if not row else self._to_domain(row)

    def upsert_active(
        self,
        channel_name: str,
        user_id: str,
        user_name: str,
        display_name: str,
        followed_at: datetime | None,
        seen_at: datetime,
    ):
        row = (
            self._db.query(ChannelFollowerRow)
            .filter_by(channel_name=channel_name, user_id=user_id)
            .first()
        )
        if row:
            row.user_name = user_name
            row.display_name = display_name
            row.followed_at = followed_at
            row.last_seen_at = seen_at
            row.unfollowed_at = None
            row.is_active = True
            row.updated_at = seen_at
        else:
            row = ChannelFollowerRow(
                channel_name=channel_name,
                user_id=user_id,
                user_name=user_name,
                display_name=display_name,
                followed_at=followed_at,
                first_seen_at=seen_at,
                last_seen_at=seen_at,
                is_active=True,
                created_at=seen_at,
                updated_at=seen_at,
            )
            self._db.add(row)

    def mark_unfollowed(self, channel_name: str, user_ids: list[str], unfollowed_at: datetime):
        if not user_ids:
            return
        (self._db.query(ChannelFollowerRow)
        .filter(ChannelFollowerRow.channel_name == channel_name, ChannelFollowerRow.user_id.in_(user_ids))
        .update({
            ChannelFollowerRow.is_active: False,
            ChannelFollowerRow.unfollowed_at: unfollowed_at,
            ChannelFollowerRow.last_seen_at: unfollowed_at,
            ChannelFollowerRow.updated_at: unfollowed_at,
        }, synchronize_session=False))
