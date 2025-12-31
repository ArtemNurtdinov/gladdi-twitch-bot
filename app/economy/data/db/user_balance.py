from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Integer, String

from core.db import Base


class UserBalance(Base):
    __tablename__ = "user_balance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_name = Column(String, nullable=False)
    user_name = Column(String, nullable=False)
    balance = Column(BigInteger, default=0, nullable=False)
    total_earned = Column(BigInteger, default=0, nullable=False)
    total_spent = Column(BigInteger, default=0, nullable=False)
    last_daily_claim = Column(DateTime, nullable=True)
    last_bonus_stream_id = Column(Integer, nullable=True)
    message_count = Column(Integer, default=0, nullable=False)
    last_activity_reward = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<UserBalance(user_name='{self.user_name}', balance={self.balance})>"
