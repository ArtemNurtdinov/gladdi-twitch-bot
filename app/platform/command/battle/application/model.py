from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class BattleDTO:
    channel_name: str
    display_name: str
    user_name: str
    command_call: str
    bot_name: str
    occurred_at: datetime
    message: str
    waiting_user: str | None = field(default=None)


@dataclass(frozen=True)
class BattleTimeoutAction:
    user_name: str
    duration_seconds: int
    reason: str


@dataclass(frozen=True)
class BattleUseCaseResult:
    messages: list[str]
    new_waiting_user: str | None
    timeout_action: BattleTimeoutAction | None
