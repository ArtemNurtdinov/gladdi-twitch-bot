from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RollDTO:
    command_prefix: str
    command_name: str
    channel_name: str
    display_name: str
    user_name: str
    bot_nick: str
    occurred_at: datetime
    amount_input: str | None
    last_roll_time: datetime | None


@dataclass(frozen=True)
class RollTimeoutAction:
    user_name: str
    duration_seconds: int
    reason: str


@dataclass(frozen=True)
class RollUseCaseResult:
    messages: list[str]
    timeout_action: RollTimeoutAction | None
    new_last_roll_time: datetime | None
