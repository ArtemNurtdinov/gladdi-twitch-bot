from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from core.db import Base


class BattleHistory(Base):
    __tablename__ = "battle_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_name = Column(String, nullable=False)
    opponent_1 = Column(String, nullable=False)
    opponent_2 = Column(String, nullable=False)
    winner = Column(String, nullable=False)
    result_text = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
