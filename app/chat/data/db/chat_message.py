from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from core.db import Base


class ChatMessage(Base):
    __tablename__ = "chat_message_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_name = Column(String, nullable=False)
    user_name = Column(String, nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
