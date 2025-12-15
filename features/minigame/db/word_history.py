from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from db.base import Base


class WordHistory(Base):
    __tablename__ = 'word_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_name = Column(String, nullable=False, index=True)
    word = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
