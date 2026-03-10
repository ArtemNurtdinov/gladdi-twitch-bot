from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RPSGame:
    channel_name: str
    start_time: datetime
    end_time: datetime
    bank: int = 500
    is_active: bool = True
    winner_choice: str | None = None
    user_choices: dict[str, str] = field(default_factory=dict)
