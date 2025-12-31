from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Integer, String

from app.betting.domain.models import RarityLevel
from core.db import Base


class BetHistory(Base):
    __tablename__ = "bet_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_name = Column(String, nullable=False)
    user_name = Column(String, nullable=False)
    slot_result = Column(String, nullable=False)  # "emoji1 | emoji2 | emoji3"
    result_type = Column(String, nullable=False)  # "jackpot", "partial", "miss"
    rarity_level = Column(Enum(RarityLevel), default=RarityLevel.COMMON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
