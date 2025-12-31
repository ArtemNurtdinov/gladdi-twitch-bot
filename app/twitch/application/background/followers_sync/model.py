from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class FollowersSyncJobDTO:
    channel_name: str
    occurred_at: datetime
