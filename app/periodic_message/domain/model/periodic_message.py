from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PeriodicMessage:
    id: int
    channel_name: str
    content: str
    use_llm: bool
    interval_minutes: int
    is_enabled: bool
    last_sent_at: datetime | None
    next_send_at: datetime | None


@dataclass(frozen=True)
class PeriodicMessageCreate:
    channel_name: str
    content: str
    use_llm: bool
    interval_minutes: int
    is_enabled: bool


@dataclass(frozen=True)
class PeriodicMessagePatch:
    id: int
    content: str | None
    use_llm: bool | None
    interval_minutes: int | None
    is_enabled: bool | None
