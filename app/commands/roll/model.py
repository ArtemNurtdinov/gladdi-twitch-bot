from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass(frozen=True)
class RollDTO:
    command_prefix: str
    command_name: str
    channel_name: str
    display_name: str
    user_name: str
    bot_nick: str
    occurred_at: datetime
    amount_input: Optional[str]
    last_roll_time: Optional[datetime]


@dataclass(frozen=True)
class RollTimeoutAction:
    user_name: str
    duration_seconds: int
    reason: str


@dataclass(frozen=True)
class RollUseCaseResult:
    messages: List[str]
    timeout_action: Optional[RollTimeoutAction]
    new_last_roll_time: Optional[datetime]
