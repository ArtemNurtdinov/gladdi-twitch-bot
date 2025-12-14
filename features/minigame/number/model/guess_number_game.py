from typing import Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class GuessNumberGame:
    channel_name: str
    target_number: int
    start_time: datetime
    end_time: datetime
    min_number: int = 1
    max_number: int = 100
    prize_amount: int = 1000
    is_active: bool = True
    winner: Optional[str] = None
    winning_time: Optional[datetime] = None