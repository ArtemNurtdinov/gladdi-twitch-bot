from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from db.base import Base


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
    
    def get_claimed_rewards_list(self) -> list:
        if not self.rewards_claimed:
            return []
        return [int(x) for x in self.rewards_claimed.split(',') if x.strip()]
    
    def add_reward(self, minutes_threshold: int) -> None:
        claimed_list = self.get_claimed_rewards_list()
        if minutes_threshold not in claimed_list:
            claimed_list.append(minutes_threshold)
            self.rewards_claimed = ','.join(map(str, sorted(claimed_list)))
            self.last_reward_claimed = datetime.utcnow()
    
    def has_reward(self, minutes_threshold: int) -> bool:
        return minutes_threshold in self.get_claimed_rewards_list()
    
    def get_current_session_minutes(self) -> int:
        if not self.is_watching or not self.session_start:
            return 0
        
        duration = datetime.utcnow() - self.session_start
        return int(duration.total_seconds() / 60)
    
    def get_total_minutes_with_current(self) -> int:
        return self.total_minutes + self.get_current_session_minutes()