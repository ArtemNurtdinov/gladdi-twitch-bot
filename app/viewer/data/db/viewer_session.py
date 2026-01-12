from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.stream.infrastructure.db.stream import Stream
from core.db import Base


class StreamViewerSession(Base):
    __tablename__ = "stream_viewer_session"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)

    stream_id: Mapped[int] = mapped_column(Integer, ForeignKey("stream.id"), nullable=False)

    channel_name: Mapped[str] = mapped_column(String, nullable=False)
    user_name: Mapped[str] = mapped_column(String, nullable=False)

    session_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    session_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    last_activity: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_watching: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    rewards_claimed: Mapped[str] = mapped_column(Text, default="", nullable=False)
    last_reward_claimed: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    stream: Mapped[Stream] = relationship("Stream", backref="viewer_sessions")

    def __repr__(self):
        return f"<StreamViewerSession(stream_id={self.stream_id}, user='{self.user_name}', minutes={self.total_minutes})>"
