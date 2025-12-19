from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from core.db import Base


class StreamViewerSession(Base):
    __tablename__ = 'stream_viewer_session'

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    stream_id = Column(Integer, ForeignKey('stream.id'), nullable=False)
    
    channel_name = Column(String, nullable=False)
    user_name = Column(String, nullable=False)
    
    session_start = Column(DateTime, nullable=True)
    session_end = Column(DateTime, nullable=True)
    total_minutes = Column(Integer, default=0, nullable=False)
    
    last_activity = Column(DateTime, nullable=True)
    is_watching = Column(Boolean, default=False, nullable=False)
    
    rewards_claimed = Column(Text, default='', nullable=False)
    last_reward_claimed = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    stream = relationship("Stream", backref="viewer_sessions")

    def __repr__(self):
        return f"<StreamViewerSession(stream_id={self.stream_id}, user='{self.user_name}', minutes={self.total_minutes})>"