from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.bot.domain.model.status import BotStatus
from core.db import Base


class BotRow(Base):
    __tablename__ = "bots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    bot_name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[BotStatus] = mapped_column(String, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
