from sqlalchemy import Column, String, DateTime, Integer, BigInteger, Enum
from datetime import datetime
from enum import Enum as PyEnum

from db.base import Base


class TransactionType(PyEnum):
    DAILY_BONUS = "DAILY_BONUS"
    BET_WIN = "BET_WIN"
    BET_LOSS = "BET_LOSS"
    BATTLE_WIN = "BATTLE_WIN"
    BATTLE_PARTICIPATION = "BATTLE_PARTICIPATION"
    ADMIN_ADJUST = "ADMIN_ADJUST"
    MESSAGE_REWARD = "MESSAGE_REWARD"
    SPECIAL_EVENT = "SPECIAL_EVENT"
    TRANSFER_SENT = "TRANSFER_SENT"
    TRANSFER_RECEIVED = "TRANSFER_RECEIVED"
    SHOP_PURCHASE = "SHOP_PURCHASE"
    MINIGAME_WIN = "MINIGAME_WIN"
    VIEWER_TIME_REWARD = "VIEWER_TIME_REWARD"


class TransactionHistory(Base):
    __tablename__ = 'transaction_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_name = Column(String, nullable=False)
    user_name = Column(String, nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    amount = Column(BigInteger, nullable=False)
    balance_before = Column(BigInteger, nullable=False)
    balance_after = Column(BigInteger, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<TransactionHistory(user='{self.user_name}', type='{self.transaction_type}', amount={self.amount})>" 