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
    
    def get_duration_minutes(self) -> int:
        if not self.ended_at:
            duration = datetime.utcnow() - self.started_at
        else:
            duration = self.ended_at - self.started_at
        
        return int(duration.total_seconds() / 60)
    
    def get_formatted_duration(self) -> str:
        minutes = self.get_duration_minutes()
        hours = minutes // 60
        mins = minutes % 60
        
        if hours > 0:
            return f"{hours}ч {mins}м"
        else:
            return f"{mins}м" 