from sqlalchemy import Column, String, Enum, DateTime, Integer
from datetime import datetime

from features.ai.message import Role
from db.base import Base


class TwitchMessage(Base):
    __tablename__ = 'twitch_messages'

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    channel_name = Column(String, nullable=False)
    role = Column(Enum(Role), nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ChatMessageLog(Base):
    __tablename__ = 'chat_message_log'

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_name = Column(String, nullable=False)
    user_name = Column(String, nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
