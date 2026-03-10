from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MinigameTickDTO:
    channel_name: str
    occurred_at: datetime
