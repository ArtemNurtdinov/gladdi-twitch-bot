from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from features.economy.db.transaction_history import TransactionType


@dataclass
class UserBalanceInfo:
    id: int
    channel_name: str
    user_name: str
    balance: int
    total_earned: int
    total_spent: int
    last_daily_claim: Optional[datetime]
    last_bonus_stream_id: Optional[int]
    message_count: int
    last_activity_reward: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@dataclass
class TransactionData:
    channel_name: str
    user_name: str
    transaction_type: TransactionType
    amount: int
    balance_before: int
    balance_after: int
    description: Optional[str]
    created_at: datetime


@dataclass
class BalanceBrief:
    user_name: str
    balance: int

