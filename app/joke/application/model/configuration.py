from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class JokesConfigurationDTO:
    channel_name: str
    interval_min: int
    interval_max: int
    last_joke_time: datetime | None
    next_joke_time: datetime | None
    is_enabled: bool
