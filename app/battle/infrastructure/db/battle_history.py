from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base


class BattleHistory(Base):
    __tablename__ = "battle_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    channel_name: Mapped[str] = mapped_column(String, nullable=False)
    opponent_1: Mapped[str] = mapped_column(String, nullable=False)
    opponent_2: Mapped[str] = mapped_column(String, nullable=False)
    winner: Mapped[str] = mapped_column(String, nullable=False)
    result_text: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
