from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TransactionType(Enum):
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


@dataclass
class UserBalanceInfo:
    id: int
    channel_name: str
    user_name: str
    balance: int
    total_earned: int
    total_spent: int
    last_daily_claim: datetime | None
    last_bonus_stream_id: int | None
    message_count: int
    last_activity_reward: datetime | None
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
    description: str | None
    created_at: datetime


@dataclass
class BalanceBrief:
    user_name: str
    balance: int


@dataclass
class DailyBonusResult:
    success: bool
    bonus_amount: int = 0
    bonus_message: str = ""
    failure_reason: str = ""


@dataclass
class TransferResult:
    success: bool
    message: str | None = None

    @classmethod
    def success_result(cls) -> "TransferResult":
        return cls(success=True)

    @classmethod
    def failure_result(cls, message: str) -> "TransferResult":
        return cls(success=False, message=message)


