from sqlalchemy import Column, String, Enum, DateTime, Integer
from datetime import datetime
from core.db import Base
from app.ai.domain.models import Role


class AIMessage(Base):
    __tablename__ = 'twitch_messages'

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    channel_name = Column(String, nullable=False)
    role = Column(Enum(Role), nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
