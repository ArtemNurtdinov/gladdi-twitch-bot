from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.stream.domain.models import StreamInfo


@dataclass
class ViewerSession:
    id: int
    stream_id: int
    channel_name: str
    user_name: str
    session_start: datetime
    session_end: Optional[datetime]
    total_minutes: int
    last_activity: Optional[datetime]
    is_watching: bool
    rewards_claimed: str
    last_reward_claimed: Optional[datetime]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    stream: StreamInfo | None = None

    def get_claimed_rewards_list(self) -> list:
        if not self.rewards_claimed:
            return []
        return [int(x) for x in self.rewards_claimed.split(',') if x.strip()]

    