from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SummarizerJobDTO:
    channel_name: str
    occurred_at: datetime
    since: datetime | None = None


@dataclass(frozen=True)
class SummarizerResult:
    summary: str | None
    advance_cursor: bool
