from sqlalchemy import Column, String, DateTime, Integer, BigInteger, Enum
from datetime import datetime
from core.db import Base
from app.economy.domain.models import TransactionType


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
