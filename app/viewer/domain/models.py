from dataclasses import dataclass
from datetime import datetime

from app.stream.domain.models import StreamInfo


@dataclass
class ViewerSession:
    id: int
    stream_id: int
    channel_name: str
    user_name: str
    session_start: datetime
    session_end: datetime | None
    total_minutes: int
    last_activity: datetime | None
    is_watching: bool
    rewards_claimed: str
    last_reward_claimed: datetime | None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    stream: StreamInfo | None = None

    def get_claimed_rewards_list(self) -> list:
        if not self.rewards_claimed:
            return []
        return [int(x) for x in self.rewards_claimed.split(",") if x.strip()]
