from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional

RPS_CHOICES = ("камень", "ножницы", "бумага")


@dataclass
class RPSGame:
    channel_name: str
    start_time: datetime
    end_time: datetime
    bank: int = 500
    is_active: bool = True
    winner_choice: Optional[str] = None
    user_choices: Dict[str, str] = field(default_factory=dict)
