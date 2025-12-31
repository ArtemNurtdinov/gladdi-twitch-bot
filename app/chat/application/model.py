from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SummarizerJobDTO:
    channel_name: str
    occurred_at: datetime
    interval_minutes: int
