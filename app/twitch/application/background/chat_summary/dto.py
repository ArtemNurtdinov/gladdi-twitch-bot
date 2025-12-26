from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ChatSummarizerDTO:
    channel_name: str
    occurred_at: datetime
    interval_minutes: int


