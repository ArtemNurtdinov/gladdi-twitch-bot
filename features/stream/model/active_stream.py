from dataclasses import dataclass
from datetime import datetime


@dataclass
class ActiveStream:
    id: int
    started_at: datetime
    game_name: str
    title: str
    max_concurrent_viewers: int
