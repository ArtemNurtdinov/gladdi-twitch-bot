from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Integer, String

from app.ai.gen.domain.models import Role
from core.db import Base


class AIMessage(Base):
    __tablename__ = 'twitch_messages'

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    channel_name = Column(String, nullable=False)
    role = Column(Enum(Role), nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
