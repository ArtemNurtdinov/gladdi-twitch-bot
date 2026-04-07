from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base


class JokesConfigurationRow(Base):
    __tablename__ = "jokes_configuration"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    channel_name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    interval_min: Mapped[int] = mapped_column(Integer, nullable=False)
    interval_max: Mapped[int] = mapped_column(Integer, nullable=False)
    last_joke_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    next_joke_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
