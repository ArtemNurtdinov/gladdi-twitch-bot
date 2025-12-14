from sqlalchemy import Column, String, DateTime, Integer, Boolean, Text
from datetime import datetime

from db.base import Base


class Stream(Base):
    __tablename__ = 'stream'

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_name = Column(String, nullable=False)
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    game_name = Column(String, nullable=True)
    title = Column(Text, nullable=True)
    total_viewers = Column(Integer, default=0, nullable=False)
    max_concurrent_viewers = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        status = "активен" if self.is_active else "завершен"
        return f"<Stream(channel='{self.channel_name}', started='{self.started_at}', status='{status}')>"