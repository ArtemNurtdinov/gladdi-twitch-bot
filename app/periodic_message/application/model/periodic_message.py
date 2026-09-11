from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PeriodicMessageDTO:
    id: int
    channel_name: str
    content: str
    use_llm: bool
    interval_minutes: int
    is_enabled: bool
    last_sent_at: datetime | None
    next_send_at: datetime | None
