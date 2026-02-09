from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.betting.domain.models import RarityLevel
from core.db import Base


class BetHistory(Base):
    __tablename__ = "bet_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    channel_name: Mapped[str] = mapped_column(String, nullable=False)
    user_name: Mapped[str] = mapped_column(String, nullable=False)
    slot_result: Mapped[str] = mapped_column(String, nullable=False)  # "emoji1 | emoji2 | emoji3"
    result_type: Mapped[str] = mapped_column(String, nullable=False)  # "jackpot", "partial", "miss"
    rarity_level: Mapped[RarityLevel] = mapped_column(Enum(RarityLevel), default=RarityLevel.COMMON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
