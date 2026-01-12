from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.follow.domain.models import ChannelFollower
from app.follow.domain.repo import FollowersRepository
from app.follow.infrastructure.db.follower import ChannelFollowerRow


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

    def list_by_channel(self, channel_name: str) -> list[ChannelFollower]:
        stmt = select(ChannelFollowerRow).where(ChannelFollowerRow.channel_name == channel_name)
        rows = self._db.execute(stmt).scalars().all()
        return [self._to_domain(row) for row in rows]

    def list_active(self, channel_name: str) -> list[ChannelFollower]:
        stmt = (
            select(ChannelFollowerRow)
            .where(ChannelFollowerRow.channel_name == channel_name)
            .where(ChannelFollowerRow.is_active.is_(True))
        )
        rows = self._db.execute(stmt).scalars().all()
        return [self._to_domain(row) for row in rows]

    def list_new_since(self, channel_name: str, since: datetime, until: datetime | None = None) -> list[ChannelFollower]:
        stmt = (
            select(ChannelFollowerRow)
            .where(ChannelFollowerRow.channel_name == channel_name)
            .where(ChannelFollowerRow.is_active.is_(True))
            .where(ChannelFollowerRow.followed_at.is_not(None))
            .where(ChannelFollowerRow.followed_at >= since)
        )
        if until:
            stmt = stmt.where(ChannelFollowerRow.followed_at <= until)
        rows = self._db.execute(stmt).scalars().all()
        return [self._to_domain(row) for row in rows]

    def list_unfollowed_since(self, channel_name: str, since: datetime, until: datetime | None = None) -> list[ChannelFollower]:
        stmt = (
            select(ChannelFollowerRow)
            .where(ChannelFollowerRow.channel_name == channel_name)
            .where(ChannelFollowerRow.is_active.is_(False))
            .where(ChannelFollowerRow.unfollowed_at.is_not(None))
            .where(ChannelFollowerRow.unfollowed_at >= since)
        )
        if until:
            stmt = stmt.where(ChannelFollowerRow.unfollowed_at <= until)
        rows = self._db.execute(stmt).scalars().all()
        return [self._to_domain(row) for row in rows]

    def get_by_user_name(self, channel_name: str, user_name: str) -> ChannelFollower | None:
        stmt = (
            select(ChannelFollowerRow)
            .where(ChannelFollowerRow.channel_name == channel_name)
            .where(ChannelFollowerRow.user_name == user_name)
        )
        row = self._db.execute(stmt).scalars().first()
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
        stmt = (
            select(ChannelFollowerRow)
            .where(ChannelFollowerRow.channel_name == channel_name)
            .where(ChannelFollowerRow.user_id == user_id)
        )
        row = self._db.execute(stmt).scalars().first()
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
        stmt = (
            update(ChannelFollowerRow)
            .where(ChannelFollowerRow.channel_name == channel_name)
            .where(ChannelFollowerRow.user_id.in_(user_ids))
            .values(
                is_active=False,
                unfollowed_at=unfollowed_at,
                last_seen_at=unfollowed_at,
                updated_at=unfollowed_at,
            )
        )
        self._db.execute(stmt)
