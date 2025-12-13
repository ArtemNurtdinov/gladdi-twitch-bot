from dataclasses import dataclass
from typing import Optional

from features.economy.db.user_balance import UserBalance


@dataclass
class DailyBonusResult:
    success: bool
    user_balance: Optional[UserBalance] = None
    bonus_amount: int = 0
    bonus_message: str = ""
    failure_reason: str = ""
