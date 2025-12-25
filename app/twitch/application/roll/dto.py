from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

from app.twitch.application.dto import ChatContextDTO


@dataclass(frozen=True)
class RollDTO(ChatContextDTO):
    amount_input: Optional[str]
    command_prefix: str
    command_name: str
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
