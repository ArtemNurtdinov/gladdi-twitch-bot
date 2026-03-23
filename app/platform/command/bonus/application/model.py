from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class BonusDTO:
    channel_name: str
    display_name: str
    user_name: str
    bot_name: str
    message: str
    occurred_at: datetime
