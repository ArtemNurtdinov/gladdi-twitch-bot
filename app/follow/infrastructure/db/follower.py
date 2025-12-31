from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, UniqueConstraint

from core.db import Base


class ChannelFollowerRow(Base):
    __tablename__ = "channel_follower"
    __table_args__ = (UniqueConstraint("channel_name", "user_id", name="uq_channel_follower_user"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_name = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    user_name = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    followed_at = Column(DateTime, nullable=True)
    first_seen_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    unfollowed_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        status = "active" if self.is_active else "inactive"
        return f"<ChannelFollowerRow channel='{self.channel_name}' user='{self.user_name}' status='{status}'>"
