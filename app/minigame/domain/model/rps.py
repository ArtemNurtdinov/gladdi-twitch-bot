from dataclasses import dataclass
from datetime import datetime


@dataclass
class RPSGame:
    channel_name: str
    start_time: datetime
    end_time: datetime
    bank: int
    is_active: bool
    winner_choice: str | None
    user_choices: dict[str, str]
